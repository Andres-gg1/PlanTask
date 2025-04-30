from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from plantask.models.project import Project, ProjectsUser
from plantask.auth.verifysession import verify_session

@view_config(route_name='my_projects', renderer='/templates/my_projects.jinja2', request_method='GET')
@verify_session
def my_projects_page(request):
    projects = projects = request.dbsession.query(Project)\
        .join(ProjectsUser, Project.id == ProjectsUser.project_id)\
        .filter(ProjectsUser.user_id == request.session.get('user_id'))\
        .all()
    return {'projects' : projects}

@view_config(route_name='create_project', renderer='/templates/create_project.jinja2', request_method='GET', permission="admin")
@verify_session
def create_project_page(request):
    return {}


@view_config(route_name='create_project', renderer='/templates/create_project.jinja2', request_method='POST', permission="admin")
@verify_session
def create_project(request):
    try:
        # Extract form data
        name = request.POST.get('name')
        description = request.POST.get('description')

        # Validate form data
        if not name or not description:
            return {"error_ping": "Please provide a name and a description for the project."}

        # Create a new project instance
        new_project = Project(
            name=name,
            description=description,
            creation_datetime=datetime.now()
        )

        # Add the project to the database
        request.dbsession.add(new_project)
        request.dbsession.flush()  # Flush to ensure the project is saved
        
        project_creator_relation = ProjectsUser(
            project_id = new_project.id,
            user_id = request.session.get('user_id'),
            role = "project_manager"
        )
        
        request.dbsession.add(project_creator_relation)
        
        request.dbsession.flush()  # Flush to ensure the project is saved
        
        

        return HTTPFound(location=request.route_url('home'))

    except SQLAlchemyError as e:
        # Handle database errors
        request.dbsession.rollback()
        return {"error_ping": "An error occurred while creating the project. Please try again."}
    
    
#CHECK WHAT PROJECT IS WITH ITS ID
@view_config(route_name='project_by_id', request_method='GET', renderer='/templates/project_pm.jinja2')
@verify_session
def project_page(request):
    try:
        # Extract project ID from the route
        project_id = int(request.matchdict.get('id'))

        # Query the database for the project
        project = request.dbsession.query(Project).filter_by(id=project_id).first()

        if not project:
            return {"error_ping": "Project not found."}

        # Check user permissions and dynamically set the renderer
        if request.has_permission('admin'):
            request.override_renderer = '/templates/project_pm.jinja2'
        else:
            request.override_renderer = '/templates/project_pm.jinja2'

        # Return the project data
        return {
            "project": project
        }

    except SQLAlchemyError as e:
        # Handle database errors
        request.dbsession.rollback()
        return {"error_ping": "An error occurred while fetching the project. Please try again."}
