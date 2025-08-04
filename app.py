import sqlite3
import os
import csv
import io
from flask import Flask, render_template, request, redirect, url_for, flash, g, jsonify, make_response
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import joblib
from datetime import datetime, timedelta
import requests
from config import DB_DIR, MODEL_DIR, AUTH_DB, FEEDBACK_DB, TRUTH_DB, MODEL_FILE, VECTORIZER_FILE
from predict_bert import predict_news
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification
import torch

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-super-secret-key-change-this-in-production'

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# News API Configuration
NEWS_API_KEY = 'your-news-api-key'  # Replace with your actual API key
NEWS_API_URL = 'https://newsapi.org/v2/top-headlines'

# Load ML Model and Vectorizer
try:
    model = joblib.load(MODEL_FILE)
    vectorizer = joblib.load(VECTORIZER_FILE)
    print("✅ Model and vectorizer loaded successfully!")
except FileNotFoundError:
    print("❌ Model files not found. Please train and save the model first.")
    model = None
    vectorizer = None

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    try:
        conn = get_db(AUTH_DB)
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        conn.close()
        if user:
            return User(user['id'], user['username'])
    except Exception as e:
        print(f"Error loading user: {e}")
    return None

# Database helper function
def get_db(db_name):
    db = sqlite3.connect(db_name)
    db.row_factory = sqlite3.Row
    return db

# Initialize databases with enhanced error handling
def init_db():
    """Initialize all required databases with proper error handling"""
    try:
        print("Initializing databases...")
        
        # Auth database
        conn = sqlite3.connect(AUTH_DB)
        conn.execute('''CREATE TABLE IF NOT EXISTS users
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         username TEXT UNIQUE NOT NULL,
                         password_hash TEXT NOT NULL)''')
        conn.commit()
        conn.close()
        print("✅ auth.db initialized")
        
        # TruthLens database for predictions
        conn = sqlite3.connect(TRUTH_DB)
        conn.execute('''CREATE TABLE IF NOT EXISTS predictions
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         user_id INTEGER NOT NULL,
                         headline TEXT NOT NULL,
                         prediction TEXT NOT NULL,
                         confidence REAL NOT NULL,
                         timestamp TEXT NOT NULL)''')
        conn.commit()
        conn.close()
        print("✅ truthlens.db initialized")
        
        # Feedback database
        conn = sqlite3.connect(FEEDBACK_DB)
        conn.execute('''CREATE TABLE IF NOT EXISTS feedback
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         prediction_id INTEGER NOT NULL,
                         user_id INTEGER NOT NULL,
                         feedback TEXT NOT NULL,
                         timestamp TEXT NOT NULL)''')
        conn.commit()
        conn.close()
        print("✅ feedback.db initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        return False

# Helper function for IST time
def get_ist_time():
    return datetime.utcnow() + timedelta(hours=5, minutes=30)

# Initialize databases on startup
print("Starting TruthLens application...")
init_db()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if not username or not password:
            flash('Username and password are required!', 'error')
            return render_template('register.html')
        
        if len(username) < 3:
            flash('Username must be at least 3 characters long!', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long!', 'error')
            return render_template('register.html')
        
        try:
            conn = get_db(AUTH_DB)
            
            # Check if user already exists
            existing_user = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
            if existing_user:
                flash('Username already exists!', 'error')
                conn.close()
                return render_template('register.html')
            
            # Create new user
            password_hash = generate_password_hash(password)
            conn.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                        (username, password_hash))
            conn.commit()
            conn.close()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            print(f"Registration error: {e}")
            flash('Registration failed. Please try again.', 'error')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if not username or not password:
            flash('Username and password are required!', 'error')
            return render_template('login.html')
        
        try:
            conn = get_db(AUTH_DB)
            user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            conn.close()
            
            if user and check_password_hash(user['password_hash'], password):
                user_obj = User(user['id'], user['username'])
                login_user(user_obj)
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password!', 'error')
                
        except Exception as e:
            print(f"Login error: {e}")
            flash('Login failed. Please try again.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# Load BERT once when Flask starts (at the top of your app.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'bert_model')
TOKENIZER_PATH = os.path.join(BASE_DIR, 'bert_tokenizer')

bert_model = DistilBertForSequenceClassification.from_pretrained(MODEL_PATH)
bert_tokenizer = DistilBertTokenizerFast.from_pretrained(TOKENIZER_PATH)
bert_model.eval()

# Now your route:
@app.route('/predict', methods=['POST'])
@login_required
def predict():
    print(f"Prediction request from user: {current_user.id}")

    headline = request.form.get('headline')
    if not headline:
        return jsonify({'error': 'No headline provided'}), 400

    headline = headline.strip()
    if len(headline) < 5:
        return jsonify({'error': 'Headline too short. Please enter a meaningful headline.'}), 400

    try:
        # BERT Prediction
        inputs = bert_tokenizer(headline, return_tensors="pt", truncation=True, padding=True)
        with torch.no_grad():
            outputs = bert_model(**inputs)
            logits = outputs.logits
            predicted_class = torch.argmax(logits, dim=1).item()
            confidence = torch.softmax(logits, dim=1)[0][predicted_class].item() * 100

        result = 'REAL' if predicted_class == 1 else 'FAKE'
        print(f"Prediction: {result}, Confidence: {confidence:.2f}%")

        # Save to DB
        try:
            conn = get_db(TRUTH_DB)
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO predictions (user_id, headline, prediction, confidence, timestamp)
                              VALUES (?, ?, ?, ?, ?)''',
                           (current_user.id, headline, result, confidence, get_ist_time().isoformat()))
            prediction_id = cursor.lastrowid
            conn.commit()
            conn.close()

            print(f"✅ Prediction stored with ID: {prediction_id}")

            return jsonify({
                'result': result,
                'confidence': f"{confidence:.2f}%",
                'prediction_id': prediction_id
            })

        except Exception as db_error:
            print(f"❌ DB Error: {db_error}")
            return jsonify({'error': 'Database error occurred'}), 500

    except Exception as e:
        print(f"❌ BERT Prediction Error: {e}")
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500

@app.route('/feedback', methods=['POST'])
@login_required
def submit_feedback():
    prediction_id = request.form.get('prediction_id')
    feedback = request.form.get('feedback')
    
    if not prediction_id or not feedback:
        return jsonify({'error': 'Missing data'}), 400
    
    if feedback not in ['accurate', 'wrong']:
        return jsonify({'error': 'Invalid feedback value'}), 400
    
    try:
        # Verify prediction exists and belongs to current user
        conn = get_db(TRUTH_DB)
        prediction = conn.execute('SELECT id FROM predictions WHERE id = ? AND user_id = ?',
                                (prediction_id, current_user.id)).fetchone()
        conn.close()
        
        if not prediction:
            return jsonify({'error': 'Prediction not found'}), 404
        
        # Check if feedback already exists
        conn = get_db(FEEDBACK_DB)
        existing_feedback = conn.execute('SELECT id FROM feedback WHERE prediction_id = ? AND user_id = ?',
                                       (prediction_id, current_user.id)).fetchone()
        
        if existing_feedback:
            # Update existing feedback
            conn.execute('UPDATE feedback SET feedback = ?, timestamp = ? WHERE prediction_id = ? AND user_id = ?',
                        (feedback, get_ist_time().isoformat(), prediction_id, current_user.id))
        else:
            # Insert new feedback
            conn.execute('''INSERT INTO feedback (prediction_id, user_id, feedback, timestamp)
                            VALUES (?, ?, ?, ?)''',
                        (prediction_id, current_user.id, feedback, get_ist_time().isoformat()))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Feedback submitted: {feedback} for prediction {prediction_id}")
        
        return jsonify({'message': 'Feedback submitted successfully'})
        
    except Exception as e:
        print(f"❌ Feedback error: {e}")
        return jsonify({'error': f'Failed to submit feedback: {str(e)}'}), 500

@app.route('/dashboard')
@login_required
def dashboard():
    print(f"Dashboard accessed by user: {current_user.id}")
    
    try:
        # Initialize default values
        total_predictions = 0
        accuracy_stats = {'accurate': 0, 'wrong': 0}
        accuracy_percentage = 0
        recent_feedback = []
        
        # Get total predictions
        try:
            conn = get_db(TRUTH_DB)
            result = conn.execute('SELECT COUNT(*) as count FROM predictions WHERE user_id = ?',
                                (current_user.id,)).fetchone()
            total_predictions = result['count'] if result else 0
            conn.close()
            print(f"Total predictions: {total_predictions}")
        except Exception as e:
            print(f"Error getting predictions: {e}")
        
        # Get feedback stats
        try:
            conn = get_db(FEEDBACK_DB)
            feedback_results = conn.execute('''SELECT feedback, COUNT(*) as count 
                                             FROM feedback WHERE user_id = ? 
                                             GROUP BY feedback''', (current_user.id,)).fetchall()
            conn.close()
            
            for result in feedback_results:
                if result['feedback'] in accuracy_stats:
                    accuracy_stats[result['feedback']] = result['count']
            
            total_feedback = accuracy_stats['accurate'] + accuracy_stats['wrong']
            accuracy_percentage = (accuracy_stats['accurate'] / total_feedback * 100) if total_feedback > 0 else 0
            
            print(f"Feedback stats: {accuracy_stats}")
        except Exception as e:
            print(f"Error getting feedback: {e}")
        
        # Get recent feedback with headlines
        try:
            conn_feedback = get_db(FEEDBACK_DB)
            conn_predictions = get_db(TRUTH_DB)            
            # Get recent feedback
            feedback_data = conn_feedback.execute('''SELECT prediction_id, feedback, timestamp 
                                                   FROM feedback WHERE user_id = ? 
                                                   ORDER BY timestamp DESC LIMIT 5''',
                                                (current_user.id,)).fetchall()
            
            recent_feedback = []
            for fb in feedback_data:
                # Get corresponding headline
                headline_data = conn_predictions.execute('SELECT headline FROM predictions WHERE id = ?',
                                                       (fb['prediction_id'],)).fetchone()
                recent_feedback.append({
                    'feedback': fb['feedback'],
                    'timestamp': fb['timestamp'],
                    'headline': headline_data['headline'] if headline_data else 'Headline not found'
                })
            
            conn_feedback.close()
            conn_predictions.close()
            
            print(f"Recent feedback count: {len(recent_feedback)}")
        except Exception as e:
            print(f"Error getting recent feedback: {e}")
        
        return render_template('dashboard.html', 
                             total_predictions=total_predictions,
                             accuracy_percentage=accuracy_percentage,
                             recent_feedback=recent_feedback,
                             accuracy_stats=accuracy_stats)
                             
    except Exception as e:
        print(f"Dashboard error: {e}")
        flash(f'Dashboard error: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/history')
@login_required
def history():
    search_query = request.args.get('search', '').strip()
    
    try:
        conn = get_db(TRUTH_DB)
        if search_query:
            predictions = conn.execute('''SELECT * FROM predictions 
                                         WHERE user_id = ? AND headline LIKE ? 
                                         ORDER BY timestamp DESC''',
                                      (current_user.id, f'%{search_query}%')).fetchall()
        else:
            predictions = conn.execute('''SELECT * FROM predictions 
                                         WHERE user_id = ? 
                                         ORDER BY timestamp DESC''',
                                      (current_user.id,)).fetchall()
        conn.close()
        
        # Convert to list of dictionaries for easier template handling
        predictions_list = [dict(row) for row in predictions]
        
        return render_template('history.html', 
                             predictions=predictions_list, 
                             search_query=search_query)
                             
    except Exception as e:
        print(f"History error: {e}")
        flash(f'Error loading history: {str(e)}', 'error')
        return render_template('history.html', predictions=[], search_query=search_query)

@app.route('/live-news')
@login_required
def live_news():
    if not NEWS_API_KEY or NEWS_API_KEY == 'your-news-api-key':
        flash('News API key not configured. Please contact administrator.', 'error')
        return render_template('live_news.html', articles=[])
    
    try:
        params = {
            'apiKey': NEWS_API_KEY,
            'language': 'en',
            'country': 'us',
            'pageSize': 20,
            'sortBy': 'publishedAt'
        }
        
        response = requests.get(NEWS_API_URL, params=params, timeout=10)
        news_data = response.json()
        
        if response.status_code == 200:
            articles = news_data.get('articles', [])
            
            # Filter and clean articles
            cleaned_articles = []
            for article in articles:
                # Skip articles with missing or removed titles
                if not article.get('title') or article['title'] in ['[Removed]', '', None]:
                    continue
                
                # Clean up the article data
                cleaned_article = {
                    'title': article.get('title', '').strip(),
                    'description': article.get('description', '').strip() if article.get('description') else None,
                    'url': article.get('url', '#'),
                    'urlToImage': article.get('urlToImage'),
                    'publishedAt': article.get('publishedAt'),
                    'source': {
                        'name': article.get('source', {}).get('name', 'Unknown Source')
                    }
                }
                
                # Only add articles with valid titles
                if len(cleaned_article['title']) > 5:
                    cleaned_articles.append(cleaned_article)
            
            print(f"Fetched {len(cleaned_articles)} valid articles")
            return render_template('live_news.html', articles=cleaned_articles)
        else:
            error_msg = news_data.get('message', 'Unknown error')
            flash(f'Error fetching news: {error_msg}', 'error')
            return render_template('live_news.html', articles=[])
    
    except requests.RequestException as e:
        print(f"News API request error: {e}")
        flash('Unable to fetch live news. Please try again later.', 'error')
        return render_template('live_news.html', articles=[])
    except Exception as e:
        print(f"Live news error: {e}")
        flash(f'Error fetching news: {str(e)}', 'error')
        return render_template('live_news.html', articles=[])


@app.route('/export-csv')
@login_required
def export_csv():
    try:
        conn = get_db(TRUTH_DB)
        predictions = conn.execute('''SELECT headline, prediction, confidence, timestamp 
                                     FROM predictions WHERE user_id = ? 
                                     ORDER BY timestamp DESC''',
                                  (current_user.id,)).fetchall()
        conn.close()
        
        if not predictions:
            flash('No prediction data to export.', 'info')
            return redirect(url_for('dashboard'))
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Headline', 'Prediction', 'Confidence (%)', 'Timestamp (IST)'])
        
        for prediction in predictions:
            writer.writerow([
                prediction['headline'], 
                prediction['prediction'], 
                f"{prediction['confidence']:.2f}",
                prediction['timestamp']
            ])
        
        output.seek(0)
        
        response = make_response(output.getvalue())
        response.headers['Content-Disposition'] = f'attachment; filename=truthlens_predictions_{current_user.username}_{datetime.now().strftime("%Y%m%d")}.csv'
        response.headers['Content-Type'] = 'text/csv'
        
        return response
        
    except Exception as e:
        print(f"Export error: {e}")
        flash(f'Error exporting data: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

# Debug route (remove in production)
@app.route('/debug-data')
@login_required
def debug_data():
    debug_info = {
        'user_id': current_user.id,
        'username': current_user.username
    }
    
    # Check predictions
    try:
        conn = get_db(TRUTH_DB)
        predictions = conn.execute('SELECT * FROM predictions WHERE user_id = ?', (current_user.id,)).fetchall()
        debug_info['predictions'] = [dict(row) for row in predictions]
        debug_info['predictions_count'] = len(predictions)
        conn.close()
    except Exception as e:
        debug_info['predictions_error'] = str(e)
    
    # Check feedback
    try:
        conn = get_db(FEEDBACK_DB)
        feedback = conn.execute('SELECT * FROM feedback WHERE user_id = ?', (current_user.id,)).fetchall()
        debug_info['feedback'] = [dict(row) for row in feedback]
        debug_info['feedback_count'] = len(feedback)
        conn.close()
    except Exception as e:
        debug_info['feedback_error'] = str(e)
    
    return jsonify(debug_info)

# Error handlers
@app.errorhandler(404)
def not_found(error):
    flash('Page not found.', 'error')
    return redirect(url_for('index'))

@app.errorhandler(500)
def internal_error(error):
    flash('An internal error occurred. Please try again.', 'error')
    return redirect(url_for('index'))

if __name__ == '__main__':
    print("TruthLens application ready!")
    print("Visit: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
