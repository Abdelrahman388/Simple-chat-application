# from flask_socketio import send, emit
# from flask_login import current_user
# from app import socketio, db
# #from app.models import Message

# @socketio.on('message')
# def handle_message(data):
#     if current_user.is_authenticated:
#         msg = Message(sender_id=current_user.id, receiver_id=data['receiver_id'], content=data['message'])
#         db.session.add(msg)
#         db.session.commit()
#         emit('new_message', {'sender': current_user.username, 'message': data['message']}, broadcast=True)
