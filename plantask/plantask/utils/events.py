from pyramid.events import subscriber
from plantask.models.user import User
from plantask.models.project import Project
from plantask.models.notification import Notification
from plantask.models.activity_log import ActivityLog
from plantask.utils.smtp_email_sender import EmailSender
from plantask.utils.event_definition import UserAddedToProjectEvent
from datetime import datetime

@subscriber(UserAddedToProjectEvent)
def handle_user_added_to_project(event: UserAddedToProjectEvent):
    print(f"[DEBUG] Evento recibido: UserAddedToProjectEvent, user_id={event.user_id}, project_id={event.project_id}")

    
    request = event.request
    project_id = event.project_id
    user_id = event.user_id

    email_sender: EmailSender = request.registry.settings['email_sender']
    

    user = request.dbsession.query(User).filter_by(id=user_id).first()
    project = request.dbsession.query(Project).filter_by(id=project_id).first()
    if not project or not user:
        print("[DEBUG] Usuario o proyecto no encontrado")
        return
    
    print(user.username)
    subject = f"You have been added to project {project.name}"
    body = f"Hello {user.username}! You have been added to project {project.name}."
    print("HOLA")


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

    print("[DEBUG] Enviando correo a:", user.email)

    notif = Notification(user_id = user.id, project_id = project.id, message = f"You have been added to the project {project.name}", time_sent = datetime.now())
    request.dbsession.add(notif)

    log = ActivityLog()
    request.dbsession.flush()

    try:
        print(f"[DEBUG] Enviando correo a: {user.email}")
        print(subject, body, user.email, html_body)
        email_sender.send_email(subject, body, user.email, html_body)
    except Exception as e:
        print(f"[ERROR] Fallo al enviar email: {e}")
