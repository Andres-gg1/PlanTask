from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_, and_
from datetime import datetime
from plantask.models.user import User
from plantask.models.chat import PersonalChat
from plantask.models.file import File
from plantask.auth.verifysession import verify_session

from sqlalchemy import or_

@view_config(route_name='chats', renderer='plantask:templates/chats.jinja2')
@verify_session
def chats_page(request):
    user_id = request.session.get('user_id')

    # Simplified query to get the other user's details
    personal_chats = request.dbsession.query(
        PersonalChat.id.label('chat_id'),
        User.username.label('username'),
        User.first_name.label('first_name'),
        User.last_name.label('last_name'),
        File.route.label('image_route')
    ).join(
        User,
        or_(
            and_(PersonalChat.user1_id == user_id, PersonalChat.user2_id == User.id),
            and_(PersonalChat.user2_id == user_id, PersonalChat.user1_id == User.id)
        )
    ).outerjoin(File, User.user_image_id == File.id).all()

    # Format the data to pass to the template
    chats = [
        {
            'username': chat.username,
            'first_name': chat.first_name,
            'last_name': chat.last_name,
            'image_route': chat.image_route
        }
        for chat in personal_chats
    ]

    return {'chats': chats}


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
