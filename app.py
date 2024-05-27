from flask import Flask, render_template, request, redirect, url_for, flash, get_flashed_messages, session, current_app, \
    jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import smtplib
import requests
import bcrypt
import os
import sqlite3
from DataManager import DataManager

# Create an instance of DataManager
data_manager_instance = DataManager()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False)
    comment = db.Column(db.Text, nullable=False)


class Cheer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    player = db.Column(db.String(50), nullable=False)
    count = db.Column(db.Integer, default=0, nullable=False)

    user = db.relationship('User', backref='cheers')


@app.route('/cheer', methods=['POST'])
def cheer():
    data = request.get_json()
    player = data.get('player')

    if player not in ['Slaf', 'Cooley']:
        return jsonify({'success': False, 'message': 'Invalid player'}), 400

    if current_user.is_authenticated:
        user_id = current_user.id

        # Check if user has already cheered for the player
        cheer = Cheer.query.filter_by(user_id=user_id, player=player).first()

        if cheer:
            cheer.count += 1
        else:
            cheer = Cheer(user_id=user_id, player=player, count=1)
            db.session.add(cheer)

        db.session.commit()

        return jsonify({'success': True, 'cheer_count': cheer.count}), 200
    else:
        return jsonify({'success': False, 'message': 'User not authenticated'}), 401


@app.route('/get_cheer_counts', methods=['GET'])
def get_cheer_counts():
    try:
        slaf_count = Cheer.query.filter_by(player='Slaf').count()
        cooley_count = Cheer.query.filter_by(player='Cooley').count()

        return jsonify({
            'success': True,
            'cheer_counts': {
                'Slaf': slaf_count,
                'Cooley': cooley_count
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.context_processor
def utility_processor():
    def get_cheer_count(player):
        cheer = Cheer.query.filter_by(player=player).first()
        return cheer.count if cheer else 0

    return dict(get_cheer_count=get_cheer_count)



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def create_database():
    with app.app_context():
        db.create_all()


@app.route('/')
def index():
    logged_in_username = current_user.username if current_user.is_authenticated else None

    (Slaf_season_games, Slaf_season_goals, Slaf_season_assists, Slaf_season_plusminus,
     Slaf_points) = data_manager_instance.Slaf_Data()
    (LC_season_games, LC_season_goals, LC_season_assists, LC_season_plusminus,
     LC_points) = data_manager_instance.LC_Data()

    comments = Comment.query.all()

    return render_template('index.html',
                           Slaf_season_games=Slaf_season_games,
                           Slaf_season_goals=Slaf_season_goals,
                           Slaf_season_assists=Slaf_season_assists,
                           Slaf_season_plusminus=Slaf_season_plusminus,
                           Slaf_points=Slaf_points,
                           LC_season_games=LC_season_games,
                           LC_season_goals=LC_season_goals,
                           LC_season_assists=LC_season_assists,
                           LC_season_plusminus=LC_season_plusminus,
                           LC_points=LC_points,
                           comments=comments,
                           logged_in_username=logged_in_username)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already exists. Please use a different email.', category='danger')
            return redirect(url_for('signup'))

        new_user = User(username=username, email=email, password=hashed_password.decode('utf-8'))
        db.session.add(new_user)
        db.session.commit()

        flash('Registered successfully! Please login.', category='success')
        return redirect(url_for('login'))

    messages = get_flashed_messages(with_categories=True)
    return render_template('signup.html', messages=messages)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            login_user(user)
            flash('Logged in successfully!', category='success')
            return redirect(url_for('index'))

        flash('Invalid email or password. Please try again.', category='danger')
        return redirect(url_for('login'))

    messages = get_flashed_messages(with_categories=True)
    return render_template('login.html', messages=messages)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', category='success')
    return redirect(url_for('index'))


@app.route('/contact', methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        phone = request.form.get("phone", "")  # Retrieve phone if provided, else default to empty string
        message = request.form["message"]

        send_email(name, email, phone, message)
        return render_template("contact.html", msg_sent=True)

    return render_template("contact.html", msg_sent=False)


@app.route('/about')
def about():
    return render_template('about.html')

@app.route("/form-entry", methods=["POST"])
def receive_data():
    data = request.form
    print(data["name"])
    print(data["email"])
    print(data["phone"])
    print(data["message"])
    return "<h1>Your message has been sent.</h1>"

@app.route('/add_comment', methods=['POST'])
@login_required
def add_comment():
    text = request.form['comment']
    new_comment = Comment(username=current_user.username, comment=text)
    db.session.add(new_comment)
    db.session.commit()
    return redirect(url_for('index'))

def send_email(name, email, phone, message):
    OWN_EMAIL = "69pythontestemail69@gmail.com"
    MY_PASSWORD = "krts xouz fpqo pary"
    email_message = f"Subject:New Message from Slaf vs. Cooley Website\n\nName: {name}\nEmail: {email}\nPhone: {phone}\nMessage:{message}"
    with smtplib.SMTP("smtp.gmail.com") as connection:
        connection.starttls()
        connection.login(user=OWN_EMAIL, password=MY_PASSWORD)
        connection.sendmail(from_addr=OWN_EMAIL, to_addrs=OWN_EMAIL, msg=email_message)

if __name__ == '__main__':
    with app.app_context():
        create_database()
    app.run(debug=True)
