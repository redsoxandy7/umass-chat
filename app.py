from flask import Flask, abort, flash, request, render_template, redirect, session, url_for, request
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
from flask_socketio import SocketIO, send, join_room, leave_room, emit, Namespace
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
#from sqlalchemy.exc import IntegrityError
import psycopg2
import os
import config

app = Flask('__name__')
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://' + config.credentials['username'] + ':' + config.credentials['password'] + '@umessage.cknifq0gxrec.us-east-1.rds.amazonaws.com/umessage'
Bootstrap(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
socketio = SocketIO(app)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True,)
    email = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(80))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password

    def __repr__(self):
        return '<User %r>' % self.username


class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=80)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=4, max=80)])
    remember = BooleanField('remember me')


class RegisterForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=80)])
    email = StringField('email', validators=[InputRequired(), Email(message='invalid email'), Length(max=80)])
    password = StringField('password', validators=[InputRequired(), Length(min=8, max=80)])


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember)
                session['username'] = form.username.data
                return redirect(url_for('index'))

        flash('Invalid Username or Password')
        return redirect(url_for('login'))

    return render_template('login.html', form=form)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        try:
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
        except:
            flash('Username or Email already exists!')
            return redirect(url_for('signup'))

    return render_template('signup.html', form=form)


@app.route('/test', methods=['GET', 'POST'])
def test():
    return render_template('test.html')


@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html', name=current_user.username)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    Session['username'] = False
    return redirect(url_for('index'))


@socketio.on('message')
def handle_message(msg):
    print('message: ' + msg)
    send(msg, broadcast=True)


@socketio.on('join')
def on_join(data):
    username = session['username']
    room = data
    join_room(room)
    send(username + ' has entered the room.', room=room)


@socketio.on('leave')
def on_leave(data):
    username = session['username']
    room = data
    leave_room(room)
    send(username + ' has left the room.', room=room)


@app.route('/rooms/<id>', methods=['GET', 'POST'])
def init_sio(id):
    print(id)
    room = '/' + id

    @socketio.on('connect', namespace=room)
    def test_connect():
        send('client has entered the room: ' + room)
        print('Client connected to ' + room)

    @socketio.on('disconnect', namespace=room)
    def test_disconnect():
        print('Client disconnected')

    @socketio.on('message', namespace=room)
    def test_message(msg):
        print(room + ' message: ' + msg)
        send(msg, broadcast=True)

    return render_template('test.html')


if __name__ == '__main__':
    app.secret_key = os.urandom(12)
    socketio.run(app)
    #app.run()
