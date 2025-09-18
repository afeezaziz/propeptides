from flask import Flask, render_template, redirect, url_for, session, request
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from authlib.integrations.flask_client import OAuth
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

# Initialize OAuth
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=app.config['GOOGLE_CLIENT_ID'],
    client_secret=app.config['GOOGLE_CLIENT_SECRET'],
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User class
class User(UserMixin):
    def __init__(self, user_info):
        self.id = user_info['sub']
        self.name = user_info.get('name')
        self.email = user_info.get('email')
        self.picture = user_info.get('picture')

@login_manager.user_loader
def load_user(user_id):
    # In a real app, you would load the user from a database
    return None  # We'll handle this in the session

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    # Generate and store state in session
    state = secrets.token_urlsafe(16)
    session['oauth_state'] = state

    redirect_uri = url_for('authorize', _external=True, _scheme='https')
    return google.authorize_redirect(redirect_uri, state=state)

@app.route('/authorize')
def authorize():
    # Verify state parameter to prevent CSRF
    returned_state = request.args.get('state')
    stored_state = session.pop('oauth_state', None)

    if not returned_state or returned_state != stored_state:
        return "Invalid state parameter", 400

    token = google.authorize_access_token()
    user_info = google.userinfo()

    # Store user info in session
    session['user'] = user_info

    # Create user object and login
    user = User(user_info)
    login_user(user)

    return redirect(url_for('dashboard'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_info = session.get('user')
    return render_template('dashboard.html', user=user_info)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
