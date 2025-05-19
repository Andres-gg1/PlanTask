from datetime import datetime
import json

from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest, HTTPNoContent

from plantask.utils.file_service import FileUploadService

from plantask.auth.verifysession import verify_session

from plantask.models.file import File

def set_uploader(request, user_id):
    """
    Set the uploader directory based on the user ID.
    """
    return FileUploadService(
        upload_dir=f'plantask/static/uploads/a_{user_id}',
        dbsession=request.dbsession,
        user_id=user_id
    )

@view_config(route_name='file_list_page', renderer='templates/list_files.jinja2', request_method='GET')
def list_files(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return HTTPBadRequest("User not authenticated")

    files = request.dbsession.query(File).all()

    return {
        "files": files  
    }

@view_config(route_name='file_upload_page', renderer='templates/upload_file.jinja2', request_method='GET')
def upload_form(request):
    return {}

@view_config(route_name='file_upload_page', renderer='templates/upload_file.jinja2', request_method='POST')
def upload_file(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return HTTPBadRequest("User not authenticated")

    if 'file' not in request.POST:
        return HTTPBadRequest("No file sent")

    file_storage = request.POST['file']
    uploader = set_uploader(request, user_id)

    try:
        result = uploader.handle_upload(file_storage, context={'type': 'task', 'action': 'task_added_file'})
        return {'message': 'Archivo subido correctamente'}
    except Exception as e:
        return {'error': str(e)}
    
@view_config(route_name='delete_file_page', renderer='templates/delete_file.jinja2', request_method='GET')
def delete_file_form(request):
    return {}

@view_config(route_name='delete_file_page', renderer='templates/delete_file.jinja2', request_method='POST')
def delete_file_action(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return HTTPBadRequest("User not authenticated")

    try:
        file_id = request.POST['file_id']
        if not file_id:
            return HTTPBadRequest("File ID not provided")
        uploader = set_uploader(request, user_id)
        result = uploader.delete_file(file_id, context={'type': 'task', 'action': 'task_removed_file',})
        print(str(result))
        if result:
            return HTTPNoContent()
        else:
            return HTTPNotFound("File not found")
    except Exception as e:
        return HTTPBadRequest(f"Error deleting file: {str(e)}")
    
@view_config(route_name='multi_upload', renderer='templates/upload_zip.jinja2', request_method='GET')
def multi_upload_asas(request):
    return {}


@view_config(route_name='multi_upload', renderer='templates/upload_zip.jinja2', request_method='POST')
def multi_upload(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return {'error': 'User not authenticated'}

    files = request.POST.getall('files')


    if not files:
        return {'error': 'No file sent'}

    uploader = set_uploader(request, user_id)

    try:
        result = uploader.handle_multiple_uploads_as_file(
            files,
            zip_name='zip_archive.zip',
            context={'type': 'task', 'action': 'task_added_file'}
        )

        if not result['bool']:
            return {'error': result['msg']}
        
        return {'message': 'Archivo subido correctamente'}
    except Exception as e:
        return {'error': str(e)}