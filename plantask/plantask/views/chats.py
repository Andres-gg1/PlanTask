from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_, and_
from datetime import datetime
from plantask.models.user import User
from plantask.models.chat import PersonalChat, ChatLog, GroupChat, groupchat_users
from plantask.models.file import File
from plantask.models.project import Project, ProjectsUser  # Add this import
from plantask.auth.verifysession import verify_session
import json

@view_config(route_name='chats', renderer='plantask:templates/chats.jinja2')
@verify_session
def chats_page(request):
    user_id = request.session.get('user_id')
    current_chat_id = request.params.get('currentChatId')

    # Query personal chats
    personal_chats = request.dbsession.query(
        PersonalChat.id.label('chat_id'),
        User.id.label('other_user_id'),
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

    # Format personal chats
    chats = [
        {
            'chat_id': chat.chat_id,
            'username': chat.username,
            'other_user_id': chat.other_user_id,
            'first_name': chat.first_name,
            'last_name': chat.last_name,
            'image_route': chat.image_route,
            'is_group': False
        }
        for chat in personal_chats
    ]
    
    # Query group chats that the user belongs to
    group_chats = request.dbsession.query(
        GroupChat.id.label('chat_id'),
        GroupChat.chat_name.label('name'),
        File.route.label('image_route')
    ).join(
        groupchat_users,
        GroupChat.id == groupchat_users.c.groupchat_id
    ).outerjoin(
        File, 
        GroupChat.image_id == File.id
    ).filter(
        groupchat_users.c.user_id == user_id
    ).all()
    
    # Add group chats to the list
    chats.extend([
        {
            'chat_id': chat.chat_id,
            'first_name': chat.name,  # Use chat_name as first_name for display
            'last_name': '',
            'username': 'group',
            'image_route': chat.image_route,
            'is_group': True
        }
        for chat in group_chats
    ])

    return {'chats': chats, 'current_chat_id': current_chat_id}


@view_config(route_name='create_message_relation', request_method='POST')
@verify_session
def create_message_relation(request):
    user_id = request.session.get('user_id')
    recipient_id = request.params.get('recipient_id')

    # Verifica si ya existe un chat personal entre estos dos usuarios (sin importar el orden)
    existing_chat = request.dbsession.query(PersonalChat).filter(
        or_(
            and_(PersonalChat.user1_id == user_id, PersonalChat.user2_id == recipient_id),
            and_(PersonalChat.user1_id == recipient_id, PersonalChat.user2_id == user_id)
        )
    ).first()

    if not existing_chat:
        new_chat = PersonalChat(
            user1_id=user_id,
            user2_id=recipient_id
        )
        request.dbsession.add(new_chat)
        request.dbsession.flush()
        chat_id = new_chat.id
    else:
        chat_id = existing_chat.id

    # Redirige a la vista de chats, pasando el chat_id como parámetro para JS
    return HTTPFound(location=request.route_url('chats', _query={'currentChatId': chat_id}))

@view_config(route_name='get_chat_messages', request_method='GET')
@verify_session
def get_chat_messages(request):
    try:
        chat_id = request.matchdict.get('chat_id')
        
        messages = request.dbsession.query(ChatLog).filter(
            ChatLog.perschat_id == chat_id
        ).order_by(ChatLog.date_sent.asc()).all()
        
        user_id = request.session.get("user_id")
        unread_messages = request.dbsession.query(ChatLog).filter(
            ChatLog.perschat_id == chat_id,
            ChatLog.sender_id != user_id,
            ChatLog.state != 'read'
        ).all()

        for msg in unread_messages:
            msg.state = 'read'

        request.dbsession.flush()
        
        messages_data = [{
            "sender_id": msg.sender_id,
            "date_sent": msg.date_sent.strftime('%Y-%m-%d %H:%M'),
            "message_cont": msg.message_cont,
            "state": msg.state
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
@verify_session
def search_users_global(request):
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
        Project.name.ilike(f'%{query}%')
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

@view_config(route_name='create_group_chat', request_method='POST')
@verify_session
def create_group_chat(request):
    try:
        user_id = request.session.get('user_id')
        group_name = request.POST.get('group_name')
        user_ids = request.POST.getall('user_ids')

        if len(user_ids) < 2:
            request.session.flash({'message': 'You must select at least two users.', 'style': 'danger'})
            return HTTPFound(location=request.route_url('chats'))

        group = GroupChat(
            chat_name=group_name,
            creation_date=datetime.now()
        )
        request.dbsession.add(group)
        request.dbsession.flush()

        # Fix: Use the correct table name 'groupchat_users' instead of 'group_chats_users'
        for uid in user_ids:
            request.dbsession.execute(
                groupchat_users.insert().values(
                    groupchat_id=group.id, 
                    user_id=int(uid)
                )
            )
        
        # Also add the creator to the group
        request.dbsession.execute(
            groupchat_users.insert().values(
                groupchat_id=group.id,
                user_id=user_id
            )
        )
        
        request.dbsession.flush()

        return HTTPFound(location=request.route_url('chats', _query={'currentChatId': group.id}))
    except Exception as e:
        print("Error creating group:", e)
        request.session.flash({'message': 'Error creating group chat.', 'style': 'danger'})
        return HTTPFound(location=request.route_url('chats'))

@view_config(route_name='get_group_chat_messages', request_method='GET')
@verify_session
def get_group_chat_messages(request):
    try:
        chat_id = request.matchdict.get('chat_id')
        user_id = request.session.get('user_id')
        
        # Check if user is member of this group chat
        is_member = request.dbsession.query(groupchat_users).filter(
            groupchat_users.c.groupchat_id == chat_id,
            groupchat_users.c.user_id == user_id
        ).first()
        
        if not is_member:
            return Response(json.dumps({"error": "Not authorized"}), status=403)
        
        # Get messages for this group chat
        messages = request.dbsession.query(
            ChatLog,
            User.first_name,
            User.last_name
        ).join(
            User, 
            ChatLog.sender_id == User.id
        ).filter(
            ChatLog.groupchat_id == chat_id
        ).order_by(ChatLog.date_sent.asc()).all()
        
        # Convert to JSON-serializable format
        messages_data = [{
            "sender_id": msg.ChatLog.sender_id,
            "sender_name": f"{msg.first_name} {msg.last_name}",
            "date_sent": msg.ChatLog.date_sent.strftime('%Y-%m-%d %H:%M'),
            "message_cont": msg.ChatLog.message_cont,
            "state": msg.ChatLog.state
        } for msg in messages]

        # Get group chat details
        group_info = request.dbsession.query(
            GroupChat.chat_name,
            GroupChat.image_id,
            File.route.label('image_route')
        ).outerjoin(
            File, 
            GroupChat.image_id == File.id
        ).filter(
            GroupChat.id == chat_id
        ).first()
        
        # Get member count
        member_count = request.dbsession.query(groupchat_users).filter(
            groupchat_users.c.groupchat_id == chat_id
        ).count()

        return Response(
            json.dumps({
                "messages": messages_data,
                "is_personal_chat": False,
                "chat_id": chat_id,
                "chat_name": group_info.chat_name if group_info else "Group Chat",
                "image_route": group_info.image_route if group_info else None,
                "member_count": member_count
            }).encode('utf-8'),
            content_type='application/json; charset=utf-8',
        )
    except SQLAlchemyError as e:
        request.dbsession.rollback()
        print(f"Database error: {str(e)}")
        return {"error": "An error occurred while fetching messages"}
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return {"error": "An unexpected error occurred"}

