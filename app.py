"""
Flask Hand Sign Detector - Local Development Server
====================================================
For local development: python app.py
For Vercel deployment: uses api/index.py

QUICK START:
1. pip install -r requirements.txt
2. python app.py
3. Open http://localhost:5000
4. Register/Login to access the app

FEATURES:
- User authentication with sessions
- Separate Train and Detect modes
- Real-time hand detection via webcam (browser)
- Record and label gesture samples
- KNN classifier (configurable K value)
- Export/import datasets as JSON
- localStorage for sample persistence per user

ARCHITECTURE:
- All hand detection runs client-side (MediaPipe CDN)
- Flask serves HTML with session management
- No backend processing needed (lightweight deployment)
"""

from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from functools import wraps
from datetime import datetime
import os
import secrets

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(16))

# Simple in-memory user store (in production, use a database)
users = {}


# ===== AUTHENTICATION HELPERS =====
def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    """Get current logged-in user"""
    if 'user_id' in session:
        return users.get(session['user_id'])
    return None


# ===== ROUTES =====
@app.route('/')
def index():
    """Root - redirect to login or menu"""
    if 'user_id' in session:
        return redirect(url_for('menu'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            return render_template('login.html', error='Username and password required')

        # Check if user exists
        if username not in users:
            return render_template('login.html', error='User not found. Please register first.')

        # Verify password
        if users[username]['password'] == password:
            session['user_id'] = username
            session['username'] = username
            return redirect(url_for('menu'))
        else:
            return render_template('login.html', error='Invalid credentials')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register new user"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if not username or not password:
            return render_template('register.html', error='Username and password required')

        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match')

        if username in users:
            return render_template('register.html', error='Username already exists')

        # Create new user
        users[username] = {
            'username': username,
            'password': password,
            'dataset': {}
        }

        session['user_id'] = username
        session['username'] = username
        return redirect(url_for('menu'))

    return render_template('register.html')


@app.route('/menu')
@login_required
def menu():
    """Main menu - choose detect or train"""
    username = session.get('username')
    return render_template('menu.html', username=username)


@app.route('/detect')
@login_required
def detect():
    """Hand sign detection page"""
    username = session.get('username')
    return render_template('detect.html', username=username)


@app.route('/train')
@login_required
def train():
    """Hand sign training/recording page"""
    username = session.get('username')
    return render_template('train.html', username=username)


@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect(url_for('login'))


# ===== API ENDPOINTS =====
@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "hand-sign-detector"})


@app.route('/api/stats', methods=['GET'])
def stats():
    """Return app statistics"""
    user = get_current_user()
    return jsonify({
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "user": session.get('username'),
        "authenticated": 'user_id' in session,
        "total_users": len(users)
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"""
╔═══════════════════════════════════════════════════════════╗
║  Hand Sign Detector Server                                ║
║  Running on http://localhost:{port}                        ║
║                                                           ║
║  Features:                                                ║
║  - User Authentication                                    ║
║  - Train Mode (Record Gestures)                          ║
║  - Detect Mode (Recognize Gestures)                      ║
║                                                           ║
║  Press Ctrl+C to stop                                     ║
╚═══════════════════════════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=port, debug=True)
