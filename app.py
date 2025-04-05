# import os 
# from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, request, flash
from models import db, User
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

# load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# @app.before_first_request
# def create_tables():
#     print("🔥 Creating tables!")
#     db.create_all()

with app.app_context():
    db.create_all()

# @app.route('/')
# def hello():
#     return 'hello, Flask!'

@app.route('/')
@login_required
def home():
    return render_template('home.html', name=current_user.name)

# if we want to implement guest user logic
# if current_user.is_authenticated:
#     name = current_user.username
# else:
#     name = 'Guest'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('home'))
        flash('Invalid credentials')
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hashed_pw = generate_password_hash(request.form['password'])
        new_user = User(name=request.form['name'],
                        username=request.form['username'],
                        email=request.form['email'],
                        password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    return render_template('auth/register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

# app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')