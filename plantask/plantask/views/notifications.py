from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPFound
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from plantask.models.notification import Notification
from plantask.auth.verifysession import verify_session

@view_config(route_name='get_notifications', renderer='json', request_method='POST')
def get_notifications(request):
    user = request.session.get('user_id')
    notifications = request.dbsession.query(Notification).filter_by(user_id=user).order_by(Notification.time_sent.desc()).all()

    return {
        'notifications': [
            {
                'message': n.message,
                'created_at': n.time_sent.strftime("%Y-%m-%d %H:%M")
            }
            for n in notifications
        ]
    }