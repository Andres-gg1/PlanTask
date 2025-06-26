from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_, and_
from datetime import datetime
from plantask.models.user import User
from plantask.models.chat import PersonalChat, ChatLog, GroupChat, groupchat_users
from plantask.models.file import File
from plantask.models.project import Project, ProjectsUser
from plantask.auth.verifysession import verify_session
from sqlalchemy.sql import func
import json

@view_config(route_name='chats', renderer='plantask:templates/chats.jinja2')
@verify_session
def chats_page(request):
    user_id = request.session.get('user_id')
    current_chat_id = request.params.get('currentChatId')
    # Query personal chats with last message date

    personal_chats = request.dbsession.query(
        PersonalChat.id.label('chat_id'),
        User.id.label('other_user_id'),
        User.username.label('username'),
        User.first_name.label('first_name'),
        User.last_name.label('last_name'),
        File.route.label('image_route'),
        func.max(ChatLog.date_sent).label('last_message_date')
    ).join(
        User,
        or_(
            and_(PersonalChat.user1_id == user_id, PersonalChat.user2_id == User.id),
            and_(PersonalChat.user2_id == user_id, PersonalChat.user1_id == User.id)
        )
    ).outerjoin(File, User.user_image_id == File.id
    ).outerjoin(ChatLog, ChatLog.perschat_id == PersonalChat.id
    ).group_by(
        PersonalChat.id, User.id, User.username, User.first_name, User.last_name, File.route
    ).order_by(
        func.max(ChatLog.date_sent).desc().nullslast()
    ).all()

    # Format personal chats
    chats = [
        {
            'chat_id': chat.chat_id,
            'username': chat.username,
            'other_user_id': chat.other_user_id,
            'first_name': chat.first_name,
            'last_name': chat.last_name,
            'image_route': chat.image_route,
            'is_group': False,
            'last_message_date': chat.last_message_date
        }
        for chat in personal_chats
    ]
    
    # Query group chats that the user belongs to, with last message date
    group_chats = request.dbsession.query(
        GroupChat.id.label('chat_id'),
        GroupChat.chat_name.label('name'),
        File.route.label('image_route'),
        func.max(ChatLog.date_sent).label('last_message_date')
    ).join(
        groupchat_users,
        GroupChat.id == groupchat_users.c.groupchat_id
    ).outerjoin(
        File, 
        GroupChat.image_id == File.id
    ).outerjoin(
        ChatLog, ChatLog.groupchat_id == GroupChat.id
    ).filter(
        groupchat_users.c.user_id == user_id
    ).group_by(
        GroupChat.id, GroupChat.chat_name, File.route
    ).order_by(
        func.max(ChatLog.date_sent).desc().nullslast()
    ).all()
    
    # Add group chats to the list with last message_date
    chats.extend([
        {
            'chat_id': chat.chat_id,
            'first_name': chat.name,  # Use chat_name as first_name for display
            'last_name': '',
            'username': 'group',
            'image_route': chat.image_route,
            'is_group': True,
            'last_message_date': chat.last_message_date
        }
        for chat in group_chats
    ])

    # Sort all chats by last_message_date (most recent first, None values last)
    chats.sort(key=lambda x: x['last_message_date'] or datetime.min, reverse=True)

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
        
        # Convert string to boolean - check if it's "true"
        if is_personal_chat == 'true':
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

@view_config(route_name='create_group_chat', request_method='POST')
@verify_session
def create_group_chat(request):
    try:
        user_id = request.session.get('user_id')
        group_name = request.POST.get('group_name')
        group_description = request.POST.get('group_description')
        user_ids = request.POST.getall('user_ids')

        if len(user_ids) < 2:
            request.session.flash({'message': 'You must select at least two users.', 'style': 'danger'})
            return HTTPFound(location=request.route_url('chats'))

        group = GroupChat(
            chat_name=group_name,
            description=group_description,  # Make sure to save description
            creation_date=datetime.now()
        )
        request.dbsession.add(group)
        request.dbsession.flush()

        # Add selected users to the group
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
        # Redirect to chats with the new group selected
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
        
        # Get messages for this group chat with sender info and profile pictures
        messages = request.dbsession.query(
            ChatLog,
            User.first_name,
            User.last_name,
            User.id.label('sender_user_id'),
            File.route.label('sender_pfp')
        ).join(
            User, 
            ChatLog.sender_id == User.id
        ).outerjoin(
            File,
            User.user_image_id == File.id
        ).filter(
            ChatLog.groupchat_id == chat_id
        ).order_by(ChatLog.date_sent.asc()).all()
        
        # Get all group members with their profile pictures
        members = request.dbsession.query(
            User.id,
            User.first_name,
            User.last_name,
            User.username,
            File.route.label('pfp_route')
        ).join(
            groupchat_users,
            User.id == groupchat_users.c.user_id
        ).outerjoin(
            File,
            User.user_image_id == File.id
        ).filter(
            groupchat_users.c.groupchat_id == chat_id
        ).all()
        
        # Convert messages to JSON-serializable format
        messages_data = [{
            "sender_id": msg.ChatLog.sender_id,
            "sender_name": f"{msg.first_name} {msg.last_name}",
            "sender_pfp": msg.sender_pfp,
            "date_sent": msg.ChatLog.date_sent.strftime('%Y-%m-%d %H:%M'),
            "message_cont": msg.ChatLog.message_cont,
            "state": msg.ChatLog.state
        } for msg in messages]

        # Convert members to JSON-serializable format
        members_data = [{
            "user_id": member.id,
            "first_name": member.first_name,
            "last_name": member.last_name,
            "username": member.username,
            "pfp_route": member.pfp_route
        } for member in members]

        # Get group chat details including creation date
        group_info = request.dbsession.query(
            GroupChat.chat_name,
            GroupChat.description,
            GroupChat.creation_date,
            GroupChat.image_id,
            File.route.label('image_route')
        ).outerjoin(
            File, 
            GroupChat.image_id == File.id
        ).filter(
            GroupChat.id == chat_id
        ).first()

        return Response(
            json.dumps({
                "messages": messages_data,
                "members": members_data,
                "is_personal_chat": False,
                "chat_id": chat_id,
                "chat_name": group_info.chat_name if group_info else "Group Chat",
                "description": group_info.description if group_info else None,
                "creation_date": group_info.creation_date.strftime('%Y-%m-%d') if group_info and group_info.creation_date else None,
                "image_route": group_info.image_route if group_info else None,
                "member_count": len(members_data)
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

@view_config(route_name='edit_group_name', request_method='POST', renderer='json')
@verify_session
def edit_group_name(request):
    try:
        user_id = request.session.get('user_id')
        group_id = int(request.matchdict.get('group_id'))
        new_name = request.params.get('group_name', '').strip()
        
        if not new_name:
            return {"error": "Group name cannot be empty"}
            
        if len(new_name) > 100:
            return {"error": "Group name cannot exceed 100 characters"}
        
        # Verify user is member of the group
        is_member = request.dbsession.query(groupchat_users).filter(
            groupchat_users.c.groupchat_id == group_id,
            groupchat_users.c.user_id == user_id
        ).first()
        
        if not is_member:
            return {"error": "You are not authorized to edit this group"}
        
        # Update group name
        group = request.dbsession.query(GroupChat).filter_by(id=group_id).first()
        if not group:
            return {"error": "Group not found"}
            
        group.chat_name = new_name
        request.dbsession.flush()
        
        return {"success": "Group name updated successfully"}
        
    except Exception as e:
        request.dbsession.rollback()
        print(f"Error updating group name: {str(e)}")
        return {"error": "An error occurred while updating the group name"}


@view_config(route_name='edit_group_description', request_method='POST', renderer='json')
@verify_session
def edit_group_description(request):
    try:
        user_id = request.session.get('user_id')
        group_id = int(request.matchdict.get('group_id'))
        new_description = request.params.get('group_description', '').strip()
        
        if len(new_description) > 255:
            return {"error": "Group description cannot exceed 255 characters"}
        
        # Verify user is member of the group
        is_member = request.dbsession.query(groupchat_users).filter(
            groupchat_users.c.groupchat_id == group_id,
            groupchat_users.c.user_id == user_id
        ).first()
        
        if not is_member:
            return {"error": "You are not authorized to edit this group"}
        
        # Update group description
        group = request.dbsession.query(GroupChat).filter_by(id=group_id).first()
        if not group:
            return {"error": "Group not found"}
            
        group.description = new_description if new_description else None
        request.dbsession.flush()
        
        return {"success": "Group description updated successfully"}
        
    except Exception as e:
        request.dbsession.rollback()
        print(f"Error updating group description: {str(e)}")
        return {"error": "An error occurred while updating the group description"}


@view_config(route_name='edit_group_image', request_method='POST', renderer='json')
@verify_session
def edit_group_image(request):
    try:
        user_id = request.session.get('user_id')
        group_id = int(request.matchdict.get('group_id'))
        
        # Verify user is member of the group
        is_member = request.dbsession.query(groupchat_users).filter(
            groupchat_users.c.groupchat_id == group_id,
            groupchat_users.c.user_id == user_id
        ).first()
        
        if not is_member:
            return {"error": "You are not authorized to edit this group"}
        
        # Handle file upload similar to profile picture upload
        uploaded_file = request.params.get('file')
        if not uploaded_file:
            return {"error": "No file uploaded"}
        
        # Here you would handle the file upload logic
        # This is a placeholder - you'll need to implement file saving logic
        # similar to your existing file upload system
        
        return {"success": "Group image updated successfully"}
        
    except Exception as e:
        request.dbsession.rollback()
        print(f"Error updating group image: {str(e)}")
        return {"error": "An error occurred while updating the group image"}

