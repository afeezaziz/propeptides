import os
import requests
from flask import redirect, url_for, session, request, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User
from datetime import datetime

login_manager = LoginManager()

class GoogleAuth:
    def __init__(self):
        self.client_id = os.environ.get('GOOGLE_CLIENT_ID')
        self.client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
        # Use environment variable for redirect URI, fallback to localhost for development
        self.redirect_uri = os.environ.get('GOOGLE_REDIRECT_URI', 'http://localhost:5000/callback')
        self.auth_url = 'https://accounts.google.com/o/oauth2/v2/auth'
        self.token_url = 'https://oauth2.googleapis.com/token'
        self.user_info_url = 'https://www.googleapis.com/oauth2/v2/userinfo'

    def get_auth_url(self):
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': 'openid email profile',
            'response_type': 'code',
            'access_type': 'offline'
        }
        return f"{self.auth_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"

    def get_token(self, code):
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': self.redirect_uri
        }
        response = requests.post(self.token_url, data=data)
        return response.json()

    def get_user_info(self, access_token):
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(self.user_info_url, headers=headers)
        return response.json()

google_auth = GoogleAuth()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for('login'))

def create_or_update_user(user_info):
    user = User.query.filter_by(google_id=user_info['id']).first()

    if user:
        # Update user information
        user.name = user_info['name']
        user.email = user_info['email']
        user.picture = user_info.get('picture')
        user.last_login = datetime.utcnow()
    else:
        # Create new user
        user = User(
            google_id=user_info['id'],
            name=user_info['name'],
            email=user_info['email'],
            picture=user_info.get('picture'),
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
        db.session.add(user)

    db.session.commit()
    return user