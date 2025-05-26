from pyramid.view import view_config
from pyramid.response import FileResponse
from pyramid.httpexceptions import HTTPFound
from plantask.models.file import File
from plantask.utils.file_service import FileUploadService
from sqlalchemy.exc import SQLAlchemyError

@view_config(route_name='file_list_page', renderer='plantask:templates/test_file_service.jinja2', request_method='GET')
def file_list_page(request):
    files = request.dbsession.query(File).all()
    return {'files': files}

@view_config(route_name='file_upload_page', request_method='POST', renderer='plantask:templates/test_file_service.jinja2')
def file_upload_page(request):
    file_storage = request.POST.get('file')
    view_name = request.POST.get('view_name', 'file_upload_page')
    user_id = request.session.get('user_id') or 54  #testing
    service = FileUploadService(
        upload_dir=request.registry.settings['upload_dir'],
        dbsession=request.dbsession,
        user_id=user_id
    )
    result = service.handle_upload(file_storage, context={'type': 'file', 'action': 'file_uploaded'}, view_name=view_name)
    request.session.flash(result['msg'])
    return HTTPFound(location=request.route_url('file_list_page'))

@view_config(route_name='multi_upload', request_method='POST', renderer='plantask:templates/test_file_service.jinja2')
def multi_upload(request):
    files = request.POST.getall('multi_files')
    view_name = request.POST.get('view_name', 'multi_upload')
    user_id = request.session.get('user_id') or 54  #testing
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
    user_id = request.session.get('user_id') or 54  #testing
    service = FileUploadService(
        upload_dir=request.registry.settings['upload_dir'],
        dbsession=request.dbsession,
        user_id=user_id
    )
    result = service.delete_file(file_id, context={'type': 'file', 'action': 'file_deleted'}, view_name=view_name)
    request.session.flash(result['msg'])
    return HTTPFound(location=request.route_url('file_list_page'))

@view_config(route_name='file_crud', request_method='GET')
def file_crud(request):
    action = request.GET.get('action')
    file_id = int(request.GET.get('file_id', 0))
    user_id = request.session.get('user_id') or 1
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
            return HTTPFound(location=request.route_url('file_list_page'))
    return HTTPFound(location=request.route_url('file_list_page'))
