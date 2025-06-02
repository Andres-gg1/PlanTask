from pyramid.events import subscriber
from plantask.models.user import User
from plantask.models.project import Project
from plantask.models.notification import Notification
from plantask.models.activity_log import ActivityLog
from plantask.utils.smtp_email_sender import EmailSender
from plantask.utils.event_definition import UserAddedToProjectEvent, TaskReadyForReviewEvent
from datetime import datetime
from plantask.models.task import Task
from plantask.models.project import ProjectsUser

@subscriber(UserAddedToProjectEvent)
def handle_user_added_to_project(event: UserAddedToProjectEvent):
    
    request = event.request
    project_id = event.project_id
    user_id = event.user_id

    email_sender: EmailSender = request.registry.settings['email_sender']

    user = request.dbsession.query(User).filter_by(id=user_id).first()
    project = request.dbsession.query(Project).filter_by(id=project_id).first()
    if not project or not user:
        print("[DEBUG] Usuario o proyecto no encontrado")
        return
    
    subject = f"You have been added to project {project.name}"
    body = f"Hello {user.username}! You have been added to project {project.name}."

    html_body = f"""
    <!DOCTYPE html>
    <html lang="en">
    <body>
        <h2>Hello {user.username}!</h2>
        <p>You have been <strong>added</strong> to the project <strong>{project.name}</strong>.</p>
        <p><em>Project Details:</em></p>
        <ul>
            <li><strong>ID:</strong> {project_id}</li>
            <li><strong>Name:</strong> {project.name}</li>
            <li><strong>Description:</strong> {project.description or "No description available."}</li>
        </ul>
        <br>
        <p>Best regards,<br>The Plantask Team</p>
    </body>
    </html>
    """

    notif = Notification(user_id = user.id, 
                        project_id = project.id, 
                        message = f"You have been added to the project {project.name}", 
                        time_sent = datetime.now()
                        )
    request.dbsession.add(notif)
    request.dbsession.flush()

    try:
        email_sender.send_email(subject, body, user.email, html_body)
    except Exception as e:
        print(f"[ERROR] Fallo al enviar email: {e}")

@subscriber(TaskReadyForReviewEvent)
def handle_task_ready_for_review(event: TaskReadyForReviewEvent):
    request = event.request
    task_id = event.task_id
    email_sender: EmailSender = request.registry.settings['email_sender']

    task = request.dbsession.query(Task).filter_by(id=task_id).first()
    if not task:
        print("[DEBUG] Task not found")
        return
    project = request.dbsession.query(Project).filter_by(id=task.project_id).first()
    if not project:
        print("[DEBUG] Project not found for task")
        return

    # Find all project managers for this project
    project_managers = request.dbsession.query(User).join(ProjectsUser).filter(
        ProjectsUser.project_id == project.id,
        ProjectsUser.role == 'project_manager'
    ).all()

    subject = f"Task '{task.task_title}' is ready for review in project {project.name}"
    body = f"The task '{task.task_title}' has been moved to 'under_review'. Please review it."
    html_body = f"""
    <!DOCTYPE html>
    <html lang=\"en\">
    <body>
        <h2>Task Ready for Review</h2>
        <p>The task <strong>{task.task_title}</strong> has been moved to <strong>Under Review</strong> in project <strong>{project.name}</strong>.</p>
        <p><em>Task Description:</em> {task.task_description or 'No description.'}</p>
        <ul>
            <li><strong>Task ID:</strong> {task.id}</li>
            <li><strong>Project:</strong> {project.name}</li>
        </ul>
        <br>
        <p>Best regards,<br>The Plantask Team</p>
    </body>
    </html>
    """
    for manager in project_managers:
        notif = Notification(user_id = manager.id, 
                            project_id = project.id, 
                            message = f"The task {task.task_title} has been moved to Under Review in project {project.name}", 
                            time_sent = datetime.now()
                            )
        request.dbsession.add(notif)
    request.dbsession.flush()

    for manager in project_managers:
        try:
            email_sender.send_email(subject, body, manager.email, html_body)
        except Exception as e:
            print(f"[ERROR] Failed to send review email to {manager.email}: {e}")
