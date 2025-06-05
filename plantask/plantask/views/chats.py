from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_
from datetime import datetime
from plantask.models.user import User
from plantask.auth.verifysession import verify_session


@view_config(route_name='chats', renderer='plantask:templates/chats.jinja2')
@verify_session
def chats_page(request):
    return {}

@view_config(route_name='search_users_global', renderer='json')
def search_users_global(request):
    query = request.params.get('q', '').strip()

    if len(query) < 2:
        return []

    results = request.dbsession.query(User).filter(
        or_(
            User.username.ilike(f'%{query}%'),
            User.first_name.ilike(f'%{query}%'),
            User.last_name.ilike(f'%{query}%')
        )
    ).limit(10).all()

    return [
        {
            "id": u.id,
            "username": u.username,
            "first_name": u.first_name,
            "last_name": u.last_name
        }
        for u in results
    ]
