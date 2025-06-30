from pyramid.view import view_config
from pyramid.response import FileResponse
from pyramid.httpexceptions import HTTPFound
from plantask.models.file import File
from plantask.utils.file_service import FileUploadService
from sqlalchemy.exc import SQLAlchemyError

@view_config(route_name='file_list_page', renderer='plantask:templates/test_file_service.jinja2', request_method='GET')
def file_list_page(request):
    files = request.dbsession.query(File).filter(File.active == True).all()
    return {'files': files}

@view_config(route_name='file_upload_page', request_method='POST')
def file_upload_page(request):
    try:
        # Extract entity_type and entity_id from the form data
        entity_type = request.POST.get('entity_type')  # e.g., 'task', 'microtask', 'project', 'profile'
        entity_id = int(request.POST.get('entity_id'))  # ID of the entity to associate the file with
        file_storage = request.POST.get('file')  # The uploaded file
        view_name = request.POST.get('view_name', 'file_upload_page')  # Optional view name for logging
        user_id = request.session.get('user_id') or 53  # Default user ID for testing

        # Initialize the FileUploadService
        service = FileUploadService(
            upload_dir=request.registry.settings['upload_dir'],
            dbsession=request.dbsession,
            user_id=user_id
        )

        # Handle the file upload and associate it with the specified entity
        result = service.handle_upload(
            file_storage=file_storage,
            context={'type': entity_type, 'action': f'{entity_type}_added_file'},
            entity_type=entity_type,
            entity_id=entity_id,
            view_name=view_name
        )

        # Flash the result message and redirect to the appropriate page
        request.session.flash(result['msg'])
        # Redirect based on entity_type (you can customize this logic as needed)
        if entity_type == 'task':
            return HTTPFound(location=request.route_url('task_by_id', id=entity_id))
        elif entity_type == 'microtask':
            return HTTPFound(location=request.route_url('microtask_by_id', id=entity_id))
        elif entity_type == 'project':
            return HTTPFound(location=request.route_url('project_by_id', id=entity_id))
        elif entity_type == 'profile_picture':
            return HTTPFound(location=request.route_url('user', id=entity_id))
        else:
            return HTTPFound(location=request.route_url('file_list_page'))  # Default fallback
    except Exception as e:
        # Handle errors and rollback the session
        request.dbsession.rollback()
        request.session.flash(f"Error uploading file: {str(e)}")
        return HTTPFound(location=request.route_url('file_list_page'))

@view_config(route_name='multi_upload', request_method='POST', renderer='plantask:templates/test_file_service.jinja2')
def multi_upload(request):
    files = request.POST.getall('multi_files')
    view_name = request.POST.get('view_name', 'multi_upload')
    user_id = request.session.get('user_id') or 53  #testing
    service = FileUploadService(
        upload_dir=request.registry.settings['upload_dir'],
        dbsession=request.dbsession,
        user_id=user_id
    )
    result = service.handle_multiple_uploads_as_file(files, context={'type': 'file', 'action': 'multi_file_uploaded'}, view_name=view_name)
    request.session.flash(result['msg'])
    return HTTPFound(location=request.route_url('file_list_page'))

@view_config(route_name='delete_file_page', request_method='POST', renderer='plantask:templates/test_file_service.jinja2')
def delete_file_page(request):
    file_id = int(request.POST.get('file_id'))
    view_name = request.POST.get('view_name', 'delete_file_page')
    user_id = request.session.get('user_id') or 53  #testing
    service = FileUploadService(
        upload_dir=request.registry.settings['upload_dir'],
        dbsession=request.dbsession,
        user_id=user_id
    )
    result = service.delete_file(file_id, context={'type': 'file', 'action': 'file_deleted'}, view_name=view_name)
    request.session.flash(result['msg'])
    return HTTPFound(location=request.route_url('file_list_page'))

def redirect_to_entity(request, entity_type, entity_id):
        if entity_type == 'task' and entity_id:
            print("entity task")
            return HTTPFound(location=request.route_url('task_by_id', id=entity_id))
        elif entity_type == 'microtask' and entity_id:
            return HTTPFound(location=request.route_url('microtask_by_id', id=entity_id))
        elif entity_type == 'project' and entity_id:
            return HTTPFound(location=request.route_url('project_by_id', id=entity_id))
        elif entity_type == 'profile_picture' and entity_id:
            return HTTPFound(location=request.route_url('user', id=entity_id))
        else:
            return HTTPFound(location=request.route_url('file_list_page'))

@view_config(route_name='file_crud', request_method='GET')
def file_crud(request):
    entity_type = request.GET.get('entity_type')
    entity_id = request.GET.get('entity_id')
    try:
        action = request.GET.get('action')
        file_id = int(request.GET.get('file_id', 0))
        user_id = request.session.get('user_id')
        service = FileUploadService(
            upload_dir=request.registry.settings['upload_dir'],
            dbsession=request.dbsession,
            user_id=user_id
        )
        if action == 'download' and file_id:
            file_info = service.download_file(file_id)
            if file_info['bool']:
                response = FileResponse(
                    file_info['file_path'],
                    request=request
                )
                response.content_disposition = f'attachment; filename="{file_info["filename"]}"'
                return response
            else:
                request.session.flash(file_info['msg'])
                return redirect_to_entity(request, entity_type, entity_id)
        return redirect_to_entity(request, entity_type, entity_id)
    except Exception as e:
        request.session.flash(f'Error downloading file: {str(e)}')
        return redirect_to_entity(request, entity_type, entity_id)

@view_config(route_name='request_download', renderer='json', request_method='POST')
def request_download(request):
    # Simple simulation - always returns success
    return {
        'success': True,
        'message': 'Download request accepted'
    }

@view_config(route_name='download_file', request_method='GET')
def handle_download_file(request):
    try:
        file_id = int(request.params.get('file_id', 0))
        user_id = request.session.get('user_id') or 53  # For testing

        service = FileUploadService(
            upload_dir=request.registry.settings['upload_dir'],
            dbsession=request.dbsession,
            user_id=user_id
        )

        file_info = service.download_file(file_id)
        if file_info.get('bool'):
            response = FileResponse(
                file_info['file_path'],
                request=request
            )
            response.content_disposition = f'attachment; filename="{file_info["filename"]}"'
            return response
        else:
            request.session.flash(file_info.get('msg', 'Download failed.'))
            return HTTPFound(location=request.referrer or request.route_url('home'))

    except Exception as e:
        request.session.flash(f'Error downloading file: {str(e)}')
        return HTTPFound(location=request.referrer or request.route_url('home'))
