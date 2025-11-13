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
import json

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(16))

USERS_FILE = 'users.json'

def load_users():
    """Load users from file"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to load users: {e}")
            return {}
    return {}

def save_users(users_data):
    """Save users to file"""
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(users_data, f, indent=2)
    except Exception as e:
        print(f"[ERROR] Failed to save users: {e}")

# Load existing users on startup
users = load_users()
print(f"[INFO] Loaded {len(users)} users from storage")

# Simple in-memory user store (in production, use a database)
# users = {}


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

        users[username] = {
            'username': username,
            'password': password,
            'dataset': {}
        }
        save_users(users)
        print(f"[INFO] New user registered: {username}")

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


@app.route('/api/detect-vision', methods=['POST'])
@login_required
def detect_vision():
    """Use AI vision model to detect hand signs"""
    try:
        data = request.json
        image_data = data.get('image')
        
        api_key = os.environ.get('AI_API_KEY')
        provider = os.environ.get('AI_PROVIDER', 'openai').lower()
        
        print(f"[DEBUG] API Key configured: {bool(api_key)}")
        print(f"[DEBUG] Provider: {provider}")
        
        if not image_data:
            return jsonify({"error": "Missing image data"}), 400
            
        if not api_key:
            return jsonify({"error": "AI_API_KEY environment variable not configured. Please set AI_API_KEY in your environment."}), 500
        
        # Remove data URL prefix if present
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        # Call appropriate API
        if provider == 'openai':
            response = call_openai_vision(image_data, api_key)
        elif provider == 'anthropic':
            response = call_anthropic_vision(image_data, api_key)
        elif provider == 'groq':
            response = call_groq_vision(image_data, api_key)
        else:
            return jsonify({"error": f"Unsupported AI provider: {provider}"}), 400
        
        return jsonify(response)
    
    except Exception as e:
        print(f"[ERROR] AI detection failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"AI detection failed: {str(e)}"}), 500


def call_openai_vision(image_base64, api_key):
    """Call OpenAI GPT-4 Vision API"""
    import requests
    
    print("[DEBUG] Calling OpenAI Vision API...")
    
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Analyze this image and identify the hand sign or gesture being shown. Respond ONLY with the name of the gesture in lowercase (e.g., 'thumbs-up', 'peace', 'ok', 'pointing', 'fist', 'open-palm', etc.). If no clear hand sign is visible, respond with 'none'."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 50
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"[DEBUG] OpenAI response status: {response.status_code}")
        
        if response.status_code == 429:
            error_data = response.json()
            print(f"[ERROR] Rate limited by OpenAI: {error_data}")
            raise requests.exceptions.HTTPError(f"429 Client Error: Too Many Requests for url: {url}")
        
        response.raise_for_status()
        result = response.json()
        
        label = result['choices'][0]['message']['content'].strip().lower()
        print(f"[DEBUG] OpenAI detected: {label}")
        
        return {
            "label": label,
            "confidence": 0.95,
            "provider": "openai"
        }
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] OpenAI API request failed: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"[ERROR] Response status: {e.response.status_code}")
            print(f"[ERROR] Response body: {e.response.text}")
        raise


def call_anthropic_vision(image_base64, api_key):
    """Call Anthropic Claude Vision API"""
    import requests
    
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01"
    }
    
    payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 50,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_base64
                        }
                    },
                    {
                        "type": "text",
                        "text": "Identify the hand sign or gesture. Respond ONLY with the gesture name in lowercase (e.g., 'thumbs-up', 'peace'). If no hand sign is visible, say 'none'."
                    }
                ]
            }
        ]
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    result = response.json()
    
    label = result['content'][0]['text'].strip().lower()
    
    return {
        "label": label,
        "confidence": 0.95,
        "provider": "anthropic"
    }


def call_groq_vision(image_base64, api_key):
    """Call Groq Vision API"""
    import requests
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": "llama-3.2-90b-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Identify the hand sign. Respond ONLY with the gesture name in lowercase (e.g., 'thumbs-up', 'peace'). If no hand is visible, say 'none'."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 50
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    result = response.json()
    
    label = result['choices'][0]['message']['content'].strip().lower()
    
    return {
        "label": label,
        "confidence": 0.95,
        "provider": "groq"
    }

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
