from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_, and_
from datetime import datetime
from plantask.models.user import User
from plantask.models.chat import PersonalChat, ChatLog
from plantask.models.file import File
from plantask.auth.verifysession import verify_session
import json
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
            'chat_id': chat.chat_id,
            'username': chat.username,
            'first_name': chat.first_name,
            'last_name': chat.last_name,
            'image_route': chat.image_route
        }
        for chat in personal_chats
    ]

    return {'chats': chats}


from pyramid.response import Response
import json

@view_config(route_name='get_personal_chat_messages', request_method='GET')
@verify_session
def get_personal_messages(request):
    try:
        chat_id = request.matchdict.get('chat_id')

        messages = request.dbsession.query(ChatLog).filter(
            ChatLog.perschat_id == chat_id
        ).order_by(ChatLog.date_sent.desc()).all()

        messages_data = [{
            "sender_id": msg.sender_id,
            "date_sent": msg.date_sent.isoformat(),
            "message_cont": msg.message_cont
        } for msg in messages]

        return Response(
            json.dumps({
                "messages": messages_data,
                "is_personal_chat": True,
                "chat_id": chat_id
            }).encode('utf-8'),
            content_type='application/json; charset=utf-8',
        )
    except SQLAlchemyError as e:
        request.dbsession.rollback()
        print(f"Database error: {str(e)}")
        return {"error_ping": "An error occurred while fetching the project. Please try again."}
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return {"error_ping": "An unexpected error occurred."}

@view_config(route_name='send_message', renderer='json', request_method='POST')
@verify_session
def send_message(request):
    try:
        user_id = request.session.get('user_id')
        chat_id = request.params.get('chat_id')
        message_content = request.params.get('message-input')
        is_personal_chat = request.params.get('is_personal_chat')
        print(f"############################{chat_id}")
        print(f"############################{message_content}")
        if is_personal_chat:
            new_message = ChatLog(
                perschat_id=chat_id,
                sender_id=user_id,
                date_sent=datetime.now(),
                message_cont=message_content,
                state='delivered'
            )
            request.dbsession.add(new_message)
            request.dbsession.flush()
        else:
            new_message = ChatLog(
                groupchat_id=chat_id,
                sender_id=user_id,
                date_sent=datetime.now(),
                message_cont=message_content,
                state='delivered'
            )
            request.dbsession.add(new_message)
            request.dbsession.flush()

        return {"success": "Message sent successfully."}
    except SQLAlchemyError as e:
        request.dbsession.rollback()
        print(f"Database error: {str(e)}")
        return {"error_ping": "An error occurred while sending the message. Please try again."}
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return {"error_ping": "An unexpected error occurred."}

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


