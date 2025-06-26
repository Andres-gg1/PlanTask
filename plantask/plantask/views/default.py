from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound, HTTPNotFound, HTTPForbidden
from plantask.models.user import User
from plantask.models.file import File
from plantask.models.task import Task
from sqlalchemy import or_, and_
from plantask.models.microtask import Microtask
from plantask.models.label import Label, LabelsTask, LabelsProjectsUser
from plantask.models.project import Project, ProjectsUser
from plantask.auth.verifysession import verify_session

@view_config(route_name='home', renderer='plantask:templates/home.jinja2')
@verify_session
def home_view(request):
    user_id = request.session.get('user_id')

    # Obtener labels del usuario por proyecto
    user_labels_by_project = {}

    labels_user_query = (
        request.dbsession.query(
            LabelsProjectsUser.labels_id,
            Project.id.label("project_id")
        )
        .join(ProjectsUser, ProjectsUser.id == LabelsProjectsUser.projects_users_id)
        .join(Project, Project.id == ProjectsUser.project_id)
        .filter(ProjectsUser.user_id == user_id)
    )

    for label_id, project_id in labels_user_query.all():
        user_labels_by_project.setdefault(project_id, set()).add(label_id)

    # Obtener proyectos del usuario
    projects_query = (
        request.dbsession.query(
            Project.id,
            Project.name,
            File.route.label("image_path")
        )
        .join(ProjectsUser, Project.id == ProjectsUser.project_id)
        .outerjoin(File, Project.project_image_id == File.id)
        .filter(
            ProjectsUser.user_id == user_id,
            ProjectsUser.active.is_(True),
            Project.active.is_(True)
        )
    )

    projects_data = []

    for project in projects_query.all():
        all_tasks = []
        user_tasks = []

        tasks = (
            request.dbsession.query(Task.id, Task.task_title, Task.status, Task.due_date)
            .filter(Task.project_id == project.id, Task.active.is_(True))
            .order_by(Task.due_date.asc())
            .all()
        )

        for task in tasks:
            microtasks = (
                request.dbsession.query(Microtask.id, Microtask.name)
                .filter(Microtask.task_id == task.id, Microtask.active.is_(True))
                .all()
            )

            labels = (
                request.dbsession.query(Label.id, Label.label_name, Label.label_hex_color)
                .join(LabelsTask, Label.id == LabelsTask.labels_id)
                .filter(LabelsTask.tasks_id == task.id)
                .all()
            )

            task_label_ids = {l.id for l in labels}

            task_data = {
                'id': task.id,
                'title': task.task_title,
                'status': task.status,
                'due_date': task.due_date,
                'microtasks': [{'id': m.id, 'name': m.name} for m in microtasks],
                'labels': [{'id': l.id, 'name': l.label_name, 'color': l.label_hex_color} for l in labels]
            }

            all_tasks.append(task_data)

            # Verifica si hay al menos un label en común
            user_label_ids = user_labels_by_project.get(project.id, set())
            if user_label_ids & task_label_ids:
                user_tasks.append(task_data)

        projects_data.append({
            'id': project.id,
            'name': project.name,
            'image_path': project.image_path,
            'your_tasks': user_tasks,
            'all_tasks': all_tasks
        })

    return {"projects": projects_data}


@view_config(route_name='user', renderer='plantask:templates/user_view.jinja2')
@verify_session
def user_view(request):
    user_id = int(request.matchdict.get('id'))

    # Only load specific fields
    user_viewing = request.dbsession.query(
        User.id,
        User.username,
        User.first_name,
        User.last_name,
        User.email,
        User.permission,
        User.user_image_id
    ).filter_by(id=user_id).first()

    user_image = request.dbsession.query(
        File.route
    ).filter_by(id = user_viewing.user_image_id).scalar()

    if not user_viewing:
        return {"error_ping": "User not found."}

    return { "user_viewing": user_viewing,
            "user_image" : user_image }


@view_config(route_name='edit_user', request_method='POST')
@verify_session
def edit_user(request):
    user_id = int(request.matchdict['id'])
    user = request.dbsession.query(User).filter_by(id=user_id).first()

    if not user:
        return HTTPNotFound("User not found.")

    if request.session.get('role') != 'admin' and request.session.get('user_id') != user_id:
        return HTTPForbidden()

    user.username = request.params.get('username', user.username)
    user.first_name = request.params.get('first_name', user.first_name)
    user.last_name = request.params.get('last_name', user.last_name)
    user.email = request.params.get('email', user.email)

    request.dbsession.flush()
    return HTTPFound(location=request.route_url('user', id=user_id))

@view_config(route_name='project_info', request_method=['GET'], renderer = "/templates/project_info.jinja2")
@verify_session
def show_project_info(request):
    return {}


@view_config(route_name='search_global', renderer='json')
@verify_session
def search_global(request):
    query = request.params.get('q', '').strip()
    user_id = request.session.get('user_id')

    if len(query) < 2:
        return []

    # Search for users
    user_results = request.dbsession.query(
        User.id,
        User.username,
        User.first_name,
        User.last_name,
        File.route.label('image_route')
    ).outerjoin(File, User.user_image_id == File.id) \
     .filter(
        or_(
            User.username.ilike(f'%{query}%'),
            User.first_name.ilike(f'%{query}%'),
            User.last_name.ilike(f'%{query}%')
        )
    ).limit(5).all()
    
    # Search for projects the user is part of
    project_results = request.dbsession.query(
        Project.id,
        Project.name.label('project_name'),
        Project.description,
        File.route.label('image_route')
    ).outerjoin(File, Project.project_image_id == File.id) \
     .join(ProjectsUser, Project.id == ProjectsUser.project_id) \
     .filter(
        ProjectsUser.user_id == user_id,
        Project.name.ilike(f'%{query}%'),
        Project.active == True
    ).limit(5).all()
        
    # Format results with type indicators
    results = []
    
    # Add users with 'user' type
    results.extend([
        {
            "id": u.id,
            "username": u.username,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "image_route": u.image_route,
            "type": "user"
        }
        for u in user_results
    ])
    
    # Add projects with 'project' type
    results.extend([
        {
            "id": p.id,
            "name": p.project_name,
            "description": p.description[:50] + "..." if p.description and len(p.description) > 50 else (p.description or ""),
            "image_route": p.image_route,
            "type": "project"
        }
        for p in project_results
    ])
    
    return results