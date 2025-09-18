from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from auth import google_auth, login_manager, create_or_update_user
from dotenv import load_dotenv
import os
import secrets

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure Flask app
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 1800  # 30 minutes
app.config['GOOGLE_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID')
app.config['GOOGLE_CLIENT_SECRET'] = os.getenv('GOOGLE_CLIENT_SECRET')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'mysql+pymysql://mariadb:0cZ0FRFBB1UPsmnTKjGfm8iofaBkb0s7JZAggtz1f3RGnqqnu7d2h6dk6zF8EGbv@104.248.150.75:33004/default')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
from models import db
db.init_app(app)

login_manager.init_app(app)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    auth_url = google_auth.get_auth_url()
    return render_template('login.html', auth_url=auth_url)

@app.route('/authorize')
def authorize():
    if 'code' not in request.args:
        flash('Authorization failed', 'error')
        return redirect(url_for('login'))

    try:
        # Get access token
        token_response = google_auth.get_token(request.args['code'])
        if 'error' in token_response:
            flash('Failed to get access token', 'error')
            return redirect(url_for('login'))

        # Get user info
        user_info = google_auth.get_user_info(token_response['access_token'])

        # Create or update user
        user = create_or_update_user(user_info)
        login_user(user)

        flash('Successfully logged in!', 'success')
        return redirect(url_for('dashboard'))

    except Exception as e:
        flash(f'Login failed: {str(e)}', 'error')
        return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    user_info = 'asd'
    return render_template('dashboard.html', user=user_info)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
