# app.py - FULL UPDATED VERSION (November 17, 2025)
# Privacy-First N-Hub CyberSeurity Class Jos (JETS) Platform
# Built by @Cyber_Jem

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import json
import random
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jets_grp2_cbt.db'
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


#========================== Edit Attempt Scores ==========================

with app.app_context():
    # configuration: change these values as needed
    username_to_update = '14011'
    increment_by = -3              # set to how much you want to increment (use new_score instead to set)
    username_to_delete = 'OTHER_USERNAME'  # replace with the username you want to delete

    # Update (increment) or create the user
    user = Attempt.query.filter_by(username=username_to_update).first()
    if user:
        user.score = (user.score or 0) + increment_by
        print(f"Updated {username_to_update} score to {user.score}.")
    else:
        user = Attempt(username=username_to_update, score=increment_by)
        db.session.add(user)
        print(f"Inserted {username_to_update} with score {user.score}.")

    # Delete another user
    to_delete = Attempt.query.filter_by(username=username_to_delete).first()
    if to_delete:
        db.session.delete(to_delete)
        print(f"Deleted user {username_to_delete}.")
    else:
        print(f"User {username_to_delete} not found in Attempt.")

    db.session.commit()

    # Print all users (username, score)
    print("Attempt entries:")
    for entry in Attempt.query.order_by(Attempt.score.desc()).all():
        print(entry.username, entry.score)