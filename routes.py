from flask import render_template, redirect, session, url_for, request, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db, login_manager
from sqlalchemy.orm import aliased
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import User, Friend, FriendRequest, Message
from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('register'))
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         user = User.query.filter_by(username=request.form['username']).first()
#         if user and check_password_hash(user.password, request.form['password']):
#             login_user(user)
#             session['user_id'] = user.id  # explicitly store the user id
#             return redirect(url_for('chat'))
#         else:
#             flash('Invalid credentials.', 'danger')
#     return render_template('login.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.json.get('username')
        password = request.json.get('password')

        if not username or not password:
            return jsonify({"msg": "Missing username or password"}), 400

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            session['user_id'] = user.id 

            access_token = create_access_token(identity=user.id)
            return jsonify(access_token=access_token), 200
        else:
            return jsonify({"msg": "Bad username or password"}), 401

    return render_template('login.html')


@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html', username=current_user.username)

@app.route('/api/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user_id = get_jwt_identity()
    return jsonify(logged_in_as=current_user_id), 200

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ----------------------
# Friend Requests Routes
# ----------------------


@app.route('/send_friend_request', methods=['POST'])
@login_required
def send_friend_request():
    friend_name = request.form.get('friend_name')
    if not friend_name:
        return jsonify({'error': 'Friend username is required.'}), 400

    friend = User.query.filter_by(username=friend_name).first()

    # if friend:
    #     print("Attempting friend request:")
    #     print("Current user ID:", current_user.id)
    #     print("Friend candidate ID:", friend.id)
    # else:
    #     print("User not found for friend_name:", friend_name)

    if friend:
        if friend.id == current_user.id:
            return jsonify({'error': 'You cannot send a friend request to yourself.'}), 400

        if FriendRequest.query.filter_by(from_user_id=current_user.id, to_user_id=friend.id).first():
            return jsonify({'error': 'Friend request already sent.'}), 400

        if Friend.query.filter_by(user_id=current_user.id, friend_id=friend.id).first():
            return jsonify({'error': 'User is already your friend.'}), 400

        new_request = FriendRequest(from_user_id=current_user.id, to_user_id=friend.id)
        db.session.add(new_request)
        db.session.commit()
        return jsonify({'message': 'Friend request sent!'})
    return jsonify({'error': 'User not found!'}), 404

@app.route('/get_friends', methods=['GET'])
@login_required
def get_friends():
    friends = Friend.query.filter_by(user_id=current_user.id).all()
    friends_list = []
    for f in friends:
        friend = User.query.get(f.friend_id)
        if friend:
            friends_list.append({'id': friend.id, 'username': friend.username})
    return jsonify(friends_list)


@app.route('/get_friend_requests', methods=['GET'])
@login_required
def get_friend_requests():
    requests_received = FriendRequest.query.filter_by(to_user_id=current_user.id).all()
    req_list = []
    for req in requests_received:
        sender = User.query.get(req.from_user_id)
        if sender:
            req_list.append({'id': req.id, 'username': sender.username})
    return jsonify(req_list)

@app.route('/accept_friend_request', methods=['POST'])
@login_required
def accept_friend_request():
    req_id = request.form['request_id']
    friend_req = FriendRequest.query.get(req_id)
    if friend_req and friend_req.to_user_id == current_user.id:
        friend1 = Friend(user_id=current_user.id, friend_id=friend_req.from_user_id)
        friend2 = Friend(user_id=friend_req.from_user_id, friend_id=current_user.id)
        db.session.add(friend1)
        db.session.add(friend2)
        db.session.delete(friend_req)
        db.session.commit()
        return jsonify({'message': 'Friend request accepted!'})
    return jsonify({'error': 'Friend request not found!'}), 404

@app.route('/delete_friend_request', methods=['POST'])
@login_required
def delete_friend_request():
    req_id = request.form['request_id']
    friend_req = FriendRequest.query.get(req_id)
    if friend_req and friend_req.to_user_id == current_user.id:
        db.session.delete(friend_req)
        db.session.commit()
        return jsonify({'message': 'Friend request declined!'})
    return jsonify({'error': 'Friend request not found!'}), 404




# ---------------
# Messages routes
# ---------------

@app.route('/send_message', methods=['POST'])
@login_required
def send_message():
    receiver = User.query.filter_by(username=request.form['receiver']).first()
    if receiver:
        message = Message(sender_id=current_user.id, receiver_id=receiver.id, content=request.form['message'])
        db.session.add(message)
        db.session.commit()
        return jsonify({'message': 'Message sent!'})
    return jsonify({'error': 'User not found!'}), 404

@app.route('/get_messages/<friend_id>', methods=['GET'])
@login_required
def get_messages(friend_id):
    sender = aliased(User)
    receiver = aliased(User)
    messages = db.session.query(
        Message,
        sender.username.label('sender_username'),
        receiver.username.label('receiver_username')
    ).join(sender, Message.sender_id == sender.id
    ).join(receiver, Message.receiver_id == receiver.id
    ).filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == friend_id)) |
        ((Message.sender_id == friend_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.timestamp).all()
    results = []
    for (msg, s_name, r_name) in messages:
        results.append({
            'senderId': msg.sender_id,
            'senderName': s_name,            
            'content': msg.content,
            'timestamp': msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        })
    return jsonify(results)






