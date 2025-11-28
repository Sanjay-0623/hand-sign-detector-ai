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
import requests

# Create Flask app
app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(16))

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

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
        try:
            users = supabase_query('users', filters={'id': session['user_id']})
            if users and len(users) > 0:
                return users[0]
        except Exception as e:
            print(f"[ERROR] Failed to get current user: {str(e)}")
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

        print(f"[DEBUG] Login attempt for username: {username}")

        if not username or not password:
            return render_template('login.html', error='Username and password required')

        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            return render_template('login.html', error='Database not configured. Please contact administrator.')

        try:
            users = supabase_query('users', filters={'username': username})
            
            if not users or len(users) == 0:
                print(f"[ERROR] User {username} not found")
                return render_template('login.html', error='User not found. Please register first.')
            
            user = users[0]
            
            # Verify password
            if user['password'] == password:
                session['user_id'] = str(user['id'])
                session['username'] = username
                print(f"[INFO] User {username} logged in successfully")
                return redirect(url_for('menu'))
            else:
                print(f"[ERROR] Invalid password for user {username}")
                return render_template('login.html', error='Invalid password')
        
        except Exception as e:
            print(f"[ERROR] Database error during login: {str(e)}")
            import traceback
            traceback.print_exc()
            return render_template('login.html', error='Login failed. Please try again.')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register new user"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        print(f"[DEBUG] Registration attempt for username: {username}")

        if not username or not password:
            return render_template('register.html', error='Username and password required')

        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match')

        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            return render_template('register.html', error='Server error: Database not configured. Contact administrator.')

        try:
            existing_users = supabase_query('users', filters={'username': username})
            
            if existing_users and len(existing_users) > 0:
                print(f"[ERROR] Username {username} already exists")
                return render_template('register.html', error='Username already exists')
            
            new_user_data = {
                'username': username,
                'password': password
            }
            new_users = supabase_query('users', method='POST', data=new_user_data)
            
            if not new_users or len(new_users) == 0:
                raise Exception("User creation returned no data")
            
            print(f"[SUCCESS] User registered: {username} (ID: {new_users[0].get('id')})")
            return redirect(url_for('login'))
        
        except Exception as e:
            error_message = str(e)
            print(f"[ERROR] Registration failed: {error_message}")
            import traceback
            traceback.print_exc()
            return render_template('register.html', error=f'Error: {error_message}')

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
        username = session.get('username')
        data = request.json
        image_data = data.get('image')
        
        api_key = os.environ.get('AI_API_KEY')
        provider = os.environ.get('AI_PROVIDER', 'openai').lower()
        
        print(f"[DEBUG] ========== AI DETECTION START ==========")
        print(f"[DEBUG] User: {username}")
        print(f"[DEBUG] API Key present: {bool(api_key)}")
        print(f"[DEBUG] API Key length: {len(api_key) if api_key else 0}")
        print(f"[DEBUG] Provider: {provider}")
        print(f"[DEBUG] Image data received: {bool(image_data)}")
        print(f"[DEBUG] Image data length: {len(image_data) if image_data else 0}")
        
        if not image_data:
            print("[ERROR] No image data provided")
            return jsonify({"error": "Missing image data"}), 400
            
        if not api_key:
            print("[ERROR] AI_API_KEY not configured")
            return jsonify({"error": "AI_API_KEY environment variable not configured. Please add your API key in project settings."}), 500
        
        # Remove data URL prefix if present
        if ',' in image_data:
            image_data = image_data.split(',')[1]
            print(f"[DEBUG] Stripped data URL prefix, new length: {len(image_data)}")
        
        print(f"[DEBUG] Calling {provider} API...")
        if provider == 'openai':
            response = call_openai_vision(image_data, api_key)
        elif provider == 'anthropic':
            response = call_anthropic_vision(image_data, api_key)
        elif provider == 'groq':
            response = call_groq_vision(image_data, api_key)
        else:
            print(f"[ERROR] Unsupported provider: {provider}")
            return jsonify({"error": f"Unsupported AI provider: {provider}"}), 400
        
        print(f"[DEBUG] AI response: {response}")
        print(f"[DEBUG] ========== AI DETECTION SUCCESS ==========")
        return jsonify(response)
    
    except Exception as e:
        print(f"[ERROR] ========== AI DETECTION FAILED ==========")
        print(f"[ERROR] Exception type: {type(e).__name__}")
        print(f"[ERROR] Exception message: {str(e)}")
        import traceback
        traceback.print_exc()
        
        error_msg = str(e)
        if '429' in error_msg or 'Too Many Requests' in error_msg:
            return jsonify({
                "error": "API rate limit exceeded. Wait 30-60 seconds and try again."
            }), 429
        elif '401' in error_msg or 'Unauthorized' in error_msg:
            return jsonify({
                "error": "Invalid API key. Check AI_API_KEY in environment variables."
            }), 401
        elif 'timeout' in error_msg.lower():
            return jsonify({
                "error": "API request timed out. Please try again."
            }), 408
        else:
            return jsonify({"error": f"Detection failed: {error_msg}"}), 500


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
        if hasattr(e.response, 'text'):
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


def supabase_query(table, method='GET', filters=None, data=None):
    """Make direct HTTP request to Supabase REST API"""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise Exception("Supabase credentials not configured")
    
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    # Add filters to URL
    if filters:
        params = []
        for key, value in filters.items():
            params.append(f"{key}=eq.{value}")
        url = f"{url}?{'&'.join(params)}"
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, timeout=10)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data, timeout=10)
        elif method == 'PATCH':
            response = requests.patch(url, headers=headers, json=data, timeout=10)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers, timeout=10)
        
        response.raise_for_status()
        return response.json() if response.text else []
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Supabase HTTP request failed: {str(e)}")
        raise
