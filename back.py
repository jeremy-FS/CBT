# app.py - FULL UPDATED VERSION (November 17, 2025)
# Privacy-First N-Hub CyberSeurity Class Jos (JETS) Platform
# Built by @Cyber_Jem

from flask import Flask, render_template, request, redirect, url_for, jsonify
from waitress import serve
from flask_sqlalchemy import SQLAlchemy
import json
import io, csv
import random
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///html_css_test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

import pytz

# Define Nigerian time zone
ng_time = pytz.timezone('Africa/Lagos')

# Use this instead of datetime.utcnow()
def now_ng():
    # print(datetime.now(ng_time))
    return datetime.now(ng_time)

    
# ====================== DATABASE MODELS ======================
# Database models
class Leaderboard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    score = db.Column(db.Integer, nullable=False)

class Attempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, default=now_ng)

class AnswerLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    attempt_id = db.Column(db.Integer, nullable=False)
    question_id = db.Column(db.Integer, nullable=False)
    user_answer = db.Column(db.String(200), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    timestamp = db.Column(db.DateTime, default=now_ng)

# Load questions
with open('html-css-cbt.json', 'r', encoding='utf-8') as f:
    questions = json.load(f)

# ====================== ROUTES ======================

@app.route('/')
def index():
    """Clean welcome page - username entry"""
    return render_template('index.html')

@app.route('/start_quiz', methods=['POST'])
def start_quiz():
    username = request.form['username'].strip()
    
    if not username:
        return render_template('index.html', error="Please enter a username")
    
    #============================= Create Access Control Function =============================
    #++++++++++++++++++++++++++++ Using allowed_users list ++++++++++++++++++++++++++++++++++++
    #  
    # allowed_users = ['04417', '04418', '04419', '04420', '04421']

    # Access control check new implimentation ensure it works
    # if username not in allowed_users:  
    #     return render_template('access_denied.html', username=username)
    
    
    quiz_questions = random.sample(questions, 50)
    return render_template('quiz.html', questions=quiz_questions, username=username)

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    username = request.form['username']
    try:
        answers = json.loads(request.form.get('answers', '{}'))
    except json.JSONDecodeError:
        answers = {}
    score = 0
    new_attempt = Attempt(username=username, score=0)
    db.session.add(new_attempt)
    db.session.flush()
    attempt_id = new_attempt.id
    for qid, user_answer in answers.items():
        for q in questions:
            if q['id'] == int(qid):
                is_correct = q['answer'] == user_answer
                score += 1 if is_correct else 0
                answer_log = AnswerLog(
                    username=username,
                    attempt_id=attempt_id,
                    question_id=int(qid),
                    user_answer=user_answer,
                    is_correct=is_correct
                )
                db.session.add(answer_log)
    new_attempt.score = score
    db.session.commit()

    # === UPDATE LEADERBOARD (BEST SCORE) ===
    user_record = Leaderboard.query.filter_by(username=username).first()
    if user_record:
        if score > user_record.score:
            user_record.score = score
    else:
        new_user = Leaderboard(username=username, score=score)
        db.session.add(new_user)
    db.session.commit()

    percentage = (score / 50) * 100
    return jsonify({'score': score, 
                    'percentage': f'{percentage:.1f}', 
                    'total': 50, 
                    'redirect': url_for('check_results', username=username)
                    })

# Helper: Get user's first attempt score
def get_first_score(username):
    first_attempt = Attempt.query.filter_by(username=username)\
        .order_by(Attempt.date.asc()).first()
    return first_attempt.score if first_attempt else 0

@app.route('/check_results')
def check_results():
    username = request.args.get('username')
    
    if not username:
        return redirect(url_for('index'))
    
    #============================= Create Access Control Function =============================
    #++++++++++++++++++++++++++++ Using allowed_users list ++++++++++++++++++++++++++++++++++++
    #  
    # allowed_users = ['04417', '04418', '04419', '04415', '04421']

    # Access control check new implimentation ensure it works
    # if username not in allowed_users:  
    #     return render_template('access_denied.html', username=username)
    
    # Check if user has any attempt
    attempt_exists = Attempt.query.filter_by(username=username).first()

    if attempt_exists:
        # Redirect to full results dashboard
        return redirect(url_for('my_results', username=username))
    else:
        # Show "no result" page
        return render_template('no_result.html', username=username)

# New route for the full personal results page
@app.route('/my_results')
def my_results():
    username = request.args.get('username')
    if not username:
        return redirect(url_for('index'))

    attempts = Attempt.query.filter_by(username=username)\
                           .order_by(Attempt.date.desc()).all()

    if not attempts:
        return render_template('no_result.html', username=username)
    
    first_score = get_first_score(username)
    best_score = max(a.score for a in attempts)
    total_attempts = len(attempts)

    return render_template('my_results.html',
                         username=username,
                         attempts=attempts,
                         best_score=best_score,
                         first_score=first_score,
                         total_attempts=total_attempts)

@app.route('/history/<username>')
def history(username):
    """Legacy support - redirect to result page"""
    return redirect(url_for('check_results', username=username))
  
@app.route('/monitor_answers/<username>/<int:attempt_id>')
def monitor_answers(username, attempt_id):
    logs = AnswerLog.query.filter_by(username=username, attempt_id=attempt_id).order_by(AnswerLog.timestamp.desc()).all()
    attempt = Attempt.query.get(attempt_id)
    # Enrich logs with question text and correct answer
    question_dict = {q['id']: {'question': q['question'], 'answer': q['answer']} for q in questions}
    enriched_logs = [
        {
            'question_id': log.question_id,
            'question': question_dict.get(log.question_id, {'question': 'Unknown Question'})['question'],
            'user_answer': log.user_answer,
            'is_correct': log.is_correct,
            'correct_answer': question_dict.get(log.question_id, {'answer': 'Unknown Answer'})['answer'],
            'timestamp': log.timestamp
        }
        for log in logs
    ]
    # Calculate score and percentage
    score = attempt.score if attempt else 0
    percentage = (score / 50) * 100 if attempt else 0
    return render_template(
        'monitor.html',
        logs=enriched_logs,
        username=username,
        attempt_id=attempt_id,
        attempt_date=attempt.date if attempt else None,
        score=score,
        percentage=f'{percentage:.1f}',
        total=50
    )






# ============ ADMIN LOGIN SYSTEM ============
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, jsonify, Response, session, flash
from functools import wraps

app.secret_key = 'jets-secret-key-e490122cde179046c602f1fa40998f49'


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('admin_logged_in') != True:
            return redirect(url_for('admin_login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # CREDENTIALS!
        if username == 'admin' and password == 'JETS2025@secure':
            session['admin_logged_in'] = True
            flash('Login successful!', 'success')
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin_scores'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('admin_scores'))

# ====================== ADMIN HANDLER ======================
from flask import Response
import csv
from io import StringIO

# Protected admin page to access the download
@app.route('/admin/scores')
@login_required
def admin_scores():
    # Simple protection - you can improve this with login/auth later
    return render_template('admin_scores.html')

@app.route('/hist/<username>')
@login_required
def hist(username):
    """Legacy support - redirect to dashboard"""
    return redirect(url_for('dashboard', username=username))

@app.route('/dashboard')
@login_required
def dashboard():
    """Personal Dashboard - Only shows current user's data"""
    username = request.args.get('username')
    if not username:
        return redirect(url_for('index'))

    # Get all attempts for this user only
    attempts = Attempt.query.filter_by(username=username)\
                           .order_by(Attempt.date.desc()).all()
    # print(attempts)

    if not attempts:
        return render_template('no_result.html', username=username)

    first_score = get_first_score(username)
    best_score = max(a.score for a in attempts)
    total_attempts = len(attempts)

    return render_template('dashboard.html',
                         username=username,
                         attempts=attempts,
                         best_score=best_score,
                         first_score=first_score,
                         total_attempts=total_attempts)

@app.route('/monit_answers/<username>/<int:attempt_id>')
@login_required
def monit_answers(username, attempt_id):
    logs = AnswerLog.query.filter_by(username=username, attempt_id=attempt_id).order_by(AnswerLog.timestamp.desc()).all()
    attempt = Attempt.query.get(attempt_id)
    # Enrich logs with question text and correct answer
    question_dict = {q['id']: {'question': q['question'], 'answer': q['answer']} for q in questions}
    enriched_logs = [
        {
            'question_id': log.question_id,
            'question': question_dict.get(log.question_id, {'question': 'Unknown Question'})['question'],
            'user_answer': log.user_answer,
            'is_correct': log.is_correct,
            'correct_answer': question_dict.get(log.question_id, {'answer': 'Unknown Answer'})['answer'],
            'timestamp': log.timestamp
        }
        for log in logs
    ]
    # Calculate score and percentage
    score = attempt.score if attempt else 0
    percentage = (score / 50) * 100 if attempt else 0
    return render_template(
        'monit.html',
        logs=enriched_logs,
        username=username,
        attempt_id=attempt_id,
        attempt_date=attempt.date if attempt else None,
        score=score,
        percentage=f'{percentage:.1f}',
        total=50
    )

@app.route('/export_first_attempts_csv')
@login_required
def export_first_attempts_csv():
    # Subquery: get the earliest attempt date for each username
    first_attempt_subquery = db.session.query(
        Attempt.username,
        db.func.min(Attempt.date).label('first_date')
    ).group_by(Attempt.username).subquery()

    # Main query: join to get the score of the first attempt
    first_attempts = db.session.query(
        Attempt.username,
        Attempt.score
    ).join(
        first_attempt_subquery,
        db.and_(
            Attempt.username == first_attempt_subquery.c.username,
            Attempt.date == first_attempt_subquery.c.first_date
        )
    ).order_by(Attempt.username).all()

    # Generate CSV in memory
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Student_ID', 'Score'])  # Header
    for row in first_attempts:
        writer.writerow([row.username, row.score])

    output.seek(0)
    return Response(
        output,
        mimetype='text/csv',
        headers={
            'Content-Disposition': 'attachment;filename=nhub_/ 50_scores.csv'
        }
    )

@app.route('/export_all_attempts_csv')
@login_required
def export_all_attempts_csv():
    # Get all users who have taken the quiz
    users = db.session.query(Attempt.username).distinct().order_by(Attempt.username).all()
    users = [u[0] for u in users]

    # Build data: username → list of scores (chronological)
    data = {}
    for username in users:
        scores = [a.score for a in Attempt.query.filter_by(username=username)
                                            .order_by(Attempt.date.asc()).all()]
        data[username] = scores

    # Generate CSV
    output = StringIO()
    writer = csv.writer(output)

    # Header: username, attempt_1, attempt_2, ...
    max_attempts = max(len(scores) for scores in data.values()) if data else 0
    header = ['Student_ID'] + [f'attempt_{i+1}' for i in range(max_attempts)]
    writer.writerow(header)

    # Rows
    for username, scores in data.items():
        row = [username] + scores + [''] * (max_attempts - len(scores))  # pad with empty
        writer.writerow(row)

    output.seek(0)
    return Response(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment;filename=nhubQuiz_all_scores.csv'}
    )


@app.route('/dashboard_data')
@login_required
def dashboard_data():
    # === LIVE BEST SCORE LEADERBOARD (Top 10) ===
    best_scores = db.session.query(
        Attempt.username,
        db.func.max(Attempt.score).label('best_score')
    ).group_by(Attempt.username)\
     .order_by(db.desc('best_score'), Attempt.username)\
     .limit(10).all()

    # === ALL USERS BEST SCORES ===
    all_best = db.session.query(
        Attempt.username,
        db.func.max(Attempt.score).label('best_score')
    ).group_by(Attempt.username)\
     .order_by(db.desc('best_score'), Attempt.username).all()

    # === FIRST ATTEMPTS (for pass/fail) ===
    first_subquery = db.session.query(
        Attempt.username,
        db.func.min(Attempt.date).label('first_date')
    ).group_by(Attempt.username).subquery()

    first_attempts = db.session.query(
        Attempt.username,
        Attempt.score
    ).join(first_subquery,
           db.and_(Attempt.username == first_subquery.c.username,
                   Attempt.date == first_subquery.c.first_date)
    ).all()

    # === TOTAL ATTEMPTS (ALL QUIZZES EVER TAKEN) ===
    total_attempts = db.session.query(Attempt).count()

    
    # first = first_attempts
    # print(first)

    # Stats
    passed = sum(1 for _, s in first_attempts if s >= 11)
    failed = len(first_attempts) - passed
    total_can = len(first_attempts)

    return jsonify({
        'leaders': [{'username': u, 'score': s} for u, s in best_scores],
        'all': [{'username': u, 'score': s} for u, s in all_best],
        'first_attempts': [{'username': u, 'score': s} for u, s in first_attempts],
        'passed': passed,
        'failed': failed,
        'total_candidates': total_can,
        'total_attempts': total_attempts   # ← THIS IS NEW
    })


# ====================== Extra Admin FUnctionality Endpoint
@app.route('/admin/rebuild_leaderboard')
@login_required
def rebuild_leaderboard():
    if request.remote_addr != '127.0.0.1':  # Only allow localhost
        return "Access denied", 403

    db.session.query(Leaderboard).delete()
    results = db.session.query(
        Attempt.username,
        db.func.max(Attempt.score)
    ).group_by(Attempt.username).all()

    for username, score in results:
        db.session.add(Leaderboard(username=username, score=score))
    db.session.commit()

    return f"Leaderboard rebuilt with {len(results)} users!"

@app.route('/admin/import_scores', methods=['GET', 'POST'])
@login_required
def import_scores():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)

        if file and file.filename.endswith('.csv'):
            try:
                # Read CSV
                stream = io.StringIO(file.stream.read().decode("UTF-8"), newline=None)
                csv_reader = csv.DictReader(stream)

                imported = 0
                updated = 0
                errors = []

                for row in csv_reader:
                    username = row.get('username', '').strip()
                    score_str = row.get('score', '').strip()

                    if not username or not score_str:
                        errors.append(f"Missing data → {row}")
                        continue

                    try:
                        score = int(score_str)
                        if score < 0 or score > 50:
                            errors.append(f"Invalid score {score} for {username}")
                            continue
                    except:
                        errors.append(f"Invalid score format for {username}")
                        continue

                    # Check if user already has an attempt
                    existing = Attempt.query.filter_by(username=username).first()

                    if existing:
                        existing.score = score
                        updated += 1
                    else:
                        new_attempt = Attempt(
                            username=username,
                            score=score,
                            date=now_ng()  # or set a fixed date if needed
                        )
                        db.session.add(new_attempt)
                        imported += 1

                db.session.commit()

                msg = f"Success! Imported: {imported}, Updated: {updated}"
                if errors:
                    msg += f" | {len(errors)} errors (check console)"
                    for e in errors[:10]:  # limit log spam
                        print(f"[IMPORT ERROR] {e}")

                flash(msg, 'success')

            except Exception as e:
                flash(f'Error processing file: {str(e)}', 'error')

            return redirect(url_for('admin_scores'))

    # GET request → show upload form
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Import Scores • JETS Admin</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: system-ui, sans-serif; background: #f4f6f9; padding: 40px; text-align: center; }
            .box { max-width: 500px; margin: 0 auto; background: white; padding: 40px; border-radius: 16px; box-shadow: 0 10px 15px rgba(0,0,0,0.1); }
            input[type="file"] { margin: 20px 0; padding: 10px; }
            button { padding: 14px 32px; background: #4a00e0; color: white; border: none; border-radius: 50px; font-size: 1.1em; cursor: pointer; }
            button:hover { background: #3a00b8; }
            .back { margin-top: 20px; }
            .back a { color: #666; text-decoration: none; }
        </style>
    </head>
    <body>
        <div class="box">
            <h1>Import Scores from CSV</h1>
            <p>CSV must have columns: <code>username</code>, <code>score</code></p>
            <form method="post" enctype="multipart/form-data">
                <input type="file" name="file" accept=".csv" required>
                <br>
                <button type="submit">Upload & Import</button>
            </form>
            <div class="back">
                <a href="/admin/scores">Back to Admin Panel</a>
            </div>
        </div>
    </body>
    </html>
    '''



# ====================== RUN APP ======================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    print("N-Hub CyberSeurity Class Jos (JETS) Platform Started")
    print("Privacy Mode: ON | Public Leaderboard: OFF")
    print("Visit: http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
    # serve(app, host='0.0.0.0', port=5000, threads=100) # Use waitress for production  


