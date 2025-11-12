"""
Flask Hand Sign Detector - Vercel Serverless Entry Point
=========================================================
This file is required for Vercel serverless deployment.
It wraps the Flask app for Vercel's Python runtime.

Features:
- User authentication with session management
- Menu routing (detect vs train)
- Dataset persistence per user
- AI vision detection using OpenAI, Anthropic, or Groq APIs
"""

from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from functools import wraps
import os
import sys
import secrets
import base64
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Create Flask app
app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(16))

# Simple in-memory user store (in production, use a database)
users = {}
user_sessions = {}
api_keys = {}


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

        if username not in users:
            return render_template('login.html', error='User not found. Please register first.')

        # Verify password
        if users[username]['password'] == password:
            session['user_id'] = username
            session['username'] = username
            return redirect(url_for('menu'))
        else:
            return render_template('login.html', error='Invalid password')

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
            'password': password
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
@app.route('/api/detect-vision', methods=['POST'])
@login_required
def detect_vision():
    """Use AI vision model to detect hand signs"""
    try:
        data = request.json
        image_data = data.get('image')  # base64 encoded image
        
        api_key = os.environ.get('AI_API_KEY')
        provider = os.environ.get('AI_PROVIDER', 'openai').lower()
        
        if not image_data:
            return jsonify({"error": "Missing image"}), 400
            
        if not api_key:
            return jsonify({"error": "AI_API_KEY not configured on server"}), 500
        
        # Remove data URL prefix if present
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        # Prepare API request based on provider
        if provider == 'openai':
            response = call_openai_vision(image_data, api_key)
        elif provider == 'anthropic':
            response = call_anthropic_vision(image_data, api_key)
        elif provider == 'groq':
            response = call_groq_vision(image_data, api_key)
        else:
            return jsonify({"error": f"Unsupported provider: {provider}"}), 400
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def call_openai_vision(image_base64, api_key):
    """Call OpenAI GPT-4 Vision API"""
    import requests
    
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
    
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    result = response.json()
    
    label = result['choices'][0]['message']['content'].strip().lower()
    
    return {
        "label": label,
        "confidence": 0.95,
        "provider": "openai"
    }


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
                        "text": "Identify the hand sign or gesture. Respond ONLY with the gesture name in lowercase (e.g., 'thumbs-up', 'peace', 'ok'). If no hand sign is visible, say 'none'."
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


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "hand-sign-detector"})


@app.route('/api/stats', methods=['GET'])
def stats():
    """Return app statistics"""
    from datetime import datetime
    user = get_current_user()
    return jsonify({
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "user": session.get('username'),
        "authenticated": 'user_id' in session
    })


# Vercel requires this handler
def handler(event, context):
    """Vercel serverless handler"""
    return app(event, context)


# For local development
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
