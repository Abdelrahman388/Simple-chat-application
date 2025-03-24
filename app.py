from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from cryptography.fernet import Fernet
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import session
import os

ENCRYPTION_KEY = b'wc-AH8uTrv7QpBvIgMK_PFlYJcBBmJbXmRvO7LnjxgM='
cipher_suite = Fernet(ENCRYPTION_KEY)

# Initialize Flask-SocketIO
app = Flask(__name__)
app.config.from_object('config.Config')

app.config['JWT_SECRET_KEY'] = '255bc9e01df7572e8ad208d9a65d78d94ed29ff600783a7e1f62d297c296ddcf'  # Change this!
app.config.update(
    SESSION_COOKIE_SECURE=True,  # Only send cookies over HTTPS
    SESSION_COOKIE_HTTPONLY=True # Prevent client-side JavaScript access
)

# Secure your app with Talisman (enforces HTTPS, etc.)
# from flask_talisman import Talisman
# Talisman(app, content_security_policy=None)

# Initialize JWTManager
from flask_jwt_extended import JWTManager
jwt = JWTManager(app)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('connect')
def handle_connect():
    user_id = session.get('user_id')
    if user_id:
        join_room(f"chat_{user_id}")
        print(f"User {user_id} connected and joined room chat_{user_id}")
    else:
        print("User connected with no user_id in session")

@socketio.on('disconnect')
def handle_disconnect():
    print("User disconnected:", session.get('user_id'))

@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)
    emit('status', {'msg': f"User {session.get('user_id')} has joined the room."}, room=room)

@socketio.on('leave')
def on_leave(data):
    room = data['room']
    leave_room(room)
    emit('status', {'msg': f"User {session.get('user_id')} has left the room."}, room=room)

@socketio.on('send_message')
def handle_message(data):
    sender_id = session.get('user_id')
    receiver_id = data['receiver_id']
    message_text = data['message']
    sender_name=User.query.get(sender_id).username
    encrypted = cipher_suite.encrypt(message_text.encode('utf-8'))
    print(f"decrypted : {message_text}")
    print(f"encrypted : {encrypted}")
    new_message = Message(sender_id=sender_id, receiver_id=receiver_id, content=encrypted)
    db.session.add(new_message)
    db.session.commit()

    room = f"chat_{receiver_id}"
    emit('receive_message', {'sender': sender_id,'senderName':sender_name, 'content': message_text}, room=room)
    # Emit message to the receiver's personal room.
    # emit('receive_message', {'sender': sender_id, 'content': message_text}, room=f"chat_{receiver_id}")

@socketio.on('typing')
def handle_typing(data):
    # data should include the room and the username of the user who is typing
    #print("Typing event received:", data) 
    room = data.get('room')
    username = data.get('username')
    if room and username:
        emit('display_typing', {'username': username}, room=room)

@socketio.on('stop_typing')
def handle_stop_typing(data):
    room = data.get('room')
    if room:
        emit('hide_typing', {}, room=room)



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))  

from routes import *

if __name__ == '__main__':
    # socketio.run(app, debug=True)
    socketio.run(app, debug=True, ssl_context=('path/to/cert.pem', 'path/to/key.pem'))





