# # app.py (only the modified route)
# from flask import Flask, render_template, request, redirect, url_for, jsonify
# from flask_sqlalchemy import SQLAlchemy
# import json
# import random
# from datetime import datetime

# app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# db = SQLAlchemy(app)

# # Database models
# class Leaderboard(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(50), unique=True, nullable=False)
#     score = db.Column(db.Integer, nullable=False)

# class Attempt(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(50), nullable=False)
#     score = db.Column(db.Integer, nullable=False)
#     date = db.Column(db.DateTime, default=datetime.utcnow)

# class AnswerLog(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(50), nullable=False)
#     attempt_id = db.Column(db.Integer, nullable=False)
#     question_id = db.Column(db.Integer, nullable=False)
#     user_answer = db.Column(db.String(200), nullable=False)
#     is_correct = db.Column(db.Boolean, nullable=False)
#     timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# # Load questions from JSON with UTF-8 encoding
# with open('questions.json', 'r', encoding='utf-8') as f:
#     questions = json.load(f)

# # Routes
# @app.route('/')
# def dashboard():
#     leaders = Leaderboard.query.order_by(Leaderboard.score.desc()).limit(10).all()
#     return render_template('dashboard.html', leaders=leaders)

# @app.route('/start_quiz', methods=['POST'])
# def start_quiz():
#     username = request.form['username'].strip()
#     if not username:
#         return render_template('dashboard.html', leaders=Leaderboard.query.order_by(Leaderboard.score.desc()).limit(10).all(), error="Username cannot be empty")
#     quiz_questions = random.sample(questions, 50)
#     return render_template('quiz.html', questions=quiz_questions, username=username)

# @app.route('/submit_quiz', methods=['POST'])
# def submit_quiz():
#     username = request.form['username']
#     try:
#         answers = json.loads(request.form.get('answers', '{}'))
#     except json.JSONDecodeError:
#         answers = {}
#     score = 0
#     new_attempt = Attempt(username=username, score=0)
#     db.session.add(new_attempt)
#     db.session.flush()
#     attempt_id = new_attempt.id
#     for qid, user_answer in answers.items():
#         for q in questions:
#             if q['id'] == int(qid):
#                 is_correct = q['answer'] == user_answer
#                 score += 1 if is_correct else 0
#                 answer_log = AnswerLog(
#                     username=username,
#                     attempt_id=attempt_id,
#                     question_id=int(qid),
#                     user_answer=user_answer,
#                     is_correct=is_correct
#                 )
#                 db.session.add(answer_log)
#     new_attempt.score = score
#     user = Leaderboard.query.filter_by(username=username).first()
#     if user:
#         if score > user.score:
#             user.score = score
#     else:
#         new_user = Leaderboard(username=username, score=score)
#         db.session.add(new_user)
#     db.session.commit()
#     percentage = (score / 20) * 100
#     return jsonify({'score': score, 'percentage': f'{percentage:.1f}', 'total': 50})

# @app.route('/history/<username>')
# def history(username):
#     attempts = Attempt.query.filter_by(username=username).order_by(Attempt.date.desc()).all()
#     return render_template('history.html', attempts=attempts, username=username)

# @app.route('/monitor_answers/<username>/<int:attempt_id>')
# def monitor_answers(username, attempt_id):
#     logs = AnswerLog.query.filter_by(username=username, attempt_id=attempt_id).order_by(AnswerLog.timestamp.desc()).all()
#     attempt = Attempt.query.get(attempt_id)
#     # Enrich logs with question text and correct answer
#     question_dict = {q['id']: {'question': q['question'], 'answer': q['answer']} for q in questions}
#     enriched_logs = [
#         {
#             'question_id': log.question_id,
#             'question': question_dict.get(log.question_id, {'question': 'Unknown Question'})['question'],
#             'user_answer': log.user_answer,
#             'is_correct': log.is_correct,
#             'correct_answer': question_dict.get(log.question_id, {'answer': 'Unknown Answer'})['answer'],
#             'timestamp': log.timestamp
#         }
#         for log in logs
#     ]
#     # Calculate score and percentage
#     score = attempt.score if attempt else 0
#     percentage = (score / 20) * 100 if attempt else 0
#     return render_template(
#         'monitor.html',
#         logs=enriched_logs,
#         username=username,
#         attempt_id=attempt_id,
#         attempt_date=attempt.date if attempt else None,
#         score=score,
#         percentage=f'{percentage:.1f}',
#         total=50
#     )

# if __name__ == '__main__':
#     with app.app_context():
#         db.create_all()
#     app.run(debug=True)