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
import time
from supabase import create_client, Client

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(16))

MIN_API_INTERVAL = 10  # Minimum seconds between API calls
AI_CACHE_DURATION = 10  # Cache results for 10 seconds
LAST_API_CALL = {}  # Track last API call time per user
AI_CACHE = {}  # Cache AI detection results

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_ANON_KEY")

try:
    if not supabase_url or not supabase_key:
        print("[ERROR] Supabase environment variables not configured")
        supabase = None
    else:
        supabase: Client = create_client(supabase_url, supabase_key)
        print(f"[INFO] Supabase client initialized with URL: {supabase_url}")
except Exception as e:
    print(f"[ERROR] Failed to initialize Supabase: {str(e)}")
    supabase = None

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
    if 'user_id' in session and supabase:
        try:
            result = supabase.table('users').select('*').eq('id', session['user_id']).execute()
            if result.data and len(result.data) > 0:
                return result.data[0]
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

        if not supabase:
            return render_template('login.html', error='Database not configured. Please contact administrator.')

        try:
            response = supabase.table('users').select('*').eq('username', username).execute()
            
            if not response.data or len(response.data) == 0:
                print(f"[ERROR] User {username} not found in database")
                return render_template('login.html', error='User not found. Please register first.')
            
            user = response.data[0]
            
            # Verify password
            if user['password'] == password:
                session['user_id'] = str(user['id'])
                session['username'] = username
                print(f"[INFO] User {username} logged in successfully")
                return redirect(url_for('menu'))
            else:
                print(f"[ERROR] Invalid password for user {username}")
                return render_template('login.html', error='Invalid credentials')
        
        except Exception as e:
            print(f"[ERROR] Database error during login: {str(e)}")
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

        if not supabase:
            return render_template('register.html', error='Database not configured. Please contact administrator.')

        try:
            existing_user = supabase.table('users').select('*').eq('username', username).execute()
            
            if existing_user.data and len(existing_user.data) > 0:
                print(f"[ERROR] Username {username} already exists")
                return render_template('register.html', error='Username already exists')
            
            # Insert new user into database
            new_user = supabase.table('users').insert({
                'username': username,
                'password': password
            }).execute()
            
            print(f"[SUCCESS] New user registered: {username}")
            return redirect(url_for('login'))
        
        except Exception as e:
            print(f"[ERROR] Database error during registration: {str(e)}")
            return render_template('register.html', error='Registration failed. Please try again.')

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
    total_users = 0
    if supabase:
        try:
            total_users = len(supabase.table('users').select('*').execute().data)
        except Exception as e:
            print(f"[ERROR] Failed to get user count: {str(e)}")
    
    return jsonify({
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "user": session.get('username'),
        "authenticated": 'user_id' in session,
        "total_users": total_users
    })


@app.route('/api/detect-vision', methods=['POST'])
@login_required
def detect_vision():
    """Use AI vision model to detect hand signs with caching and rate limiting"""
    try:
        username = session.get('username')
        data = request.json
        image_data = data.get('image')
        
        api_key = os.environ.get('AI_API_KEY')
        provider = os.environ.get('AI_PROVIDER', 'openai').lower()
        
        print(f"[DEBUG] API Key configured: {bool(api_key)}")
        print(f"[DEBUG] Provider: {provider}")
        print(f"[DEBUG] User: {username}")
        
        if not image_data:
            return jsonify({"error": "Missing image data"}), 400
            
        if not api_key:
            return jsonify({"error": "AI_API_KEY environment variable not configured. Please add your OpenAI API key in Vercel project settings."}), 500
        
        current_time = time.time()
        if username in LAST_API_CALL:
            time_since_last = current_time - LAST_API_CALL[username]
            if time_since_last < MIN_API_INTERVAL:
                wait_time = int(MIN_API_INTERVAL - time_since_last)
                return jsonify({
                    "error": f"Please wait {wait_time} seconds before making another AI detection request to avoid rate limiting."
                }), 429
        
        cache_key = f"{username}_{hash(image_data[:100])}"  # Use partial hash for cache key
        if cache_key in AI_CACHE:
            cached_result, cached_time = AI_CACHE[cache_key]
            if current_time - cached_time < AI_CACHE_DURATION:
                print(f"[DEBUG] Returning cached result for {username}")
                return jsonify(cached_result)
        
        # Remove data URL prefix if present
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        LAST_API_CALL[username] = current_time
        
        # Call appropriate API
        if provider == 'openai':
            response = call_openai_vision(image_data, api_key)
        elif provider == 'anthropic':
            response = call_anthropic_vision(image_data, api_key)
        elif provider == 'groq':
            response = call_groq_vision(image_data, api_key)
        else:
            return jsonify({"error": f"Unsupported AI provider: {provider}"}), 400
        
        AI_CACHE[cache_key] = (response, current_time)
        
        if len(AI_CACHE) > 100:
            cutoff_time = current_time - AI_CACHE_DURATION
            AI_CACHE.clear()  # Simple cleanup
        
        return jsonify(response)
    
    except Exception as e:
        print(f"[ERROR] AI detection failed: {str(e)}")
        import traceback
        traceback.print_exc()
        
        error_msg = str(e)
        if '429' in error_msg or 'Too Many Requests' in error_msg:
            return jsonify({
                "error": "OpenAI rate limit exceeded. Please wait 30-60 seconds before trying again. Consider using KNN mode instead for real-time detection."
            }), 429
        elif '401' in error_msg or 'Unauthorized' in error_msg:
            return jsonify({
                "error": "Invalid API key. Please check your AI_API_KEY environment variable."
            }), 401
        else:
            return jsonify({"error": f"AI detection failed: {error_msg}"}), 500


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
                        "text": "Analyze this image and identify the hand sign being shown. If it's a letter of the alphabet (A-Z), respond with ONLY that single letter. If it's a gesture like thumbs-up, peace sign, ok sign, pointing, fist, or open palm, respond with the gesture name in lowercase. If no clear hand sign is visible, respond with 'none'. Be concise - respond with just one word or letter."
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
        "max_tokens": 10,
        "temperature": 0.3
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
                        "text": "Identify the hand sign. Respond ONLY with the gesture name in lowercase. If no hand is visible, say 'none'."
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
