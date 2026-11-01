# ================================================
#   JETS CBT – BULK IMPORT & MANAGEMENT TOOL
#   Full standalone script • No Flask web routes
#   Works directly with your existing database.db
#   Built by @Cyber_Jem – 2025
# ================================================

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import csv
import pytz
from datetime import datetime

# ------------------- Flask + DB Setup -------------------
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nhub_cyber_test1.db'   # ← change if your db has another name/path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Nigerian timezone
ng_tz = pytz.timezone('Africa/Lagos')
def now_ng():
    return datetime.now(ng_tz)

# ------------------- Your Existing Models -------------------
class Attempt(db.Model):
    __tablename__ = 'attempt'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, index=True)
    score = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, default=now_ng)

class AnswerLog(db.Model):
    __tablename__ = 'answer_log'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    attempt_id = db.Column(db.Integer, nullable=False)
    question_id = db.Column(db.Integer, nullable=False)
    user_answer = db.Column(db.String(200), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    timestamp = db.Column(db.DateTime, default=now_ng)

# (If you still have Leaderboard table – optional)
# class Leaderboard(db.Model): ...

# ====================== CORE FUNCTIONS ======================

def bulk_import_attempts(
    csv_path: str,
    username_col: int | str = 0,
    score_col: int | str = 1,
    date_col: int | str = None,
    date_format: str = "%Y-%m-%d %H:%M:%S",
    has_header: bool = True,
    delimiter: str = ","
) -> dict:
    """
    Flexible CSV importer – supports many layouts.
    Examples:
        username,score
        user_id,final_score,exam_date
        14001,45
    """
    created = updated = skipped = 0

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=delimiter)
        header = None
        if has_header:
            header = next(reader)
            # Convert column names to indices if needed
            if isinstance(username_col, str):
                username_col = header.index(username_col)
            if isinstance(score_col, str):
                score_col = header.index(score_col)
            if date_col is not None and isinstance(date_col, str):
                date_col = header.index(date_col)

        for row_num, row in enumerate(reader, start=2 if has_header else 1):
            if not row or all(cell.strip() == "" for cell in row):
                continue

            username = str(row[username_col]).strip()
            try:
                score = int(row[score_col].strip())
            except (ValueError, IndexError) as e:
                print(f"Row {row_num} → invalid score: {row}")
                skipped += 1
                continue

            # Parse date if column exists
            attempt_date = datetime.now(ng_tz)
            if date_col is not None:
                try:
                    raw = row[date_col].strip()
                    if raw:
                        attempt_date = datetime.strptime(raw, date_format)
                        attempt_date = ng_tz.localize(attempt_date)
                except Exception as e:
                    print(f"Row {row_num} → bad date '{row[date_col]}' → using now()")

            # Upsert
            existing = Attempt.query.filter_by(username=username).first()
            if existing:
                existing.score = score
                existing.date = attempt_date
                updated += 1
                print(f"Updated → {username} : {score}")
            else:
                new = Attempt(username=username, score=score, date=attempt_date)
                db.session.add(new)
                created += 1
                print(f"Created → {username} : {score}")

    db.session.commit()
    print(f"\nIMPORT COMPLETE → Created: {created} | Updated: {updated} | Skipped: {skipped}\n")
    return {"created": created, "updated": updated, "skipped": skipped}


def edit_attempt_score(username: str, new_score: int = None, increment_by: int = None) -> bool:
    attempt = Attempt.query.filter_by(username=username).first()
    if not attempt:
        print(f"User {username} not found!")
        return False

    if new_score is not None:
        old = attempt.score
        attempt.score = new_score
        print(f"{username}: {old} → {new_score} (set)")
    elif increment_by is not None:
        old = attempt.score
        attempt.score += increment_by
        print(f"{username}: {old} → {attempt.score} (+{increment_by})")
    else:
        print("Nothing to change.")
        return False

    db.session.commit()
    return True


def delete_attempt(username: str) -> bool:
    attempt = Attempt.query.filter_by(username=username).first()
    if not attempt:
        print(f"User {username} not found!")
        return False
    db.session.delete(attempt)
    db.session.commit()
    print(f"Deleted {username}")
    return True


def print_all_attempts():
    print("\nALL ATTEMPTS (sorted by score descending)".center(60, "="))
    for a in Attempt.query.order_by(Attempt.score.desc(), Attempt.username).all():
        print(f"{a.username:<12} | Score: {a.score:<3} | {a.date.strftime('%Y-%m-%d %H:%M')}")
    print("="*60 + "\n")


# ====================== RUN SCRIPT ======================
if __name__ == "__main__":
    with app.app_context():
        print("JETS CBT – Bulk Database Tool")
        print("Database: database.db\n")

        # CHANGE THIS LINE TO YOUR CSV FILE
        CSV_FILE = "nhub_cyber_test1.csv"   # ← put your file name here

        # # === IMPORT / UPDATE FROM CSV ===
        # bulk_import_attempts(
        #     csv_path=CSV_FILE,
        #     has_header=True,           # set False if no header
        #     # username ='Student_ID',  # uncomment + change if using column names
        #     # score ='Score',
        #     # date_col='exam_date',
        #     # date_format='%d/%m/%Y'
        # )

        # === OPTIONAL: Manual edits ===
        # edit_attempt_score("14011", new_score=50)
        # edit_attempt_score("14025", increment_by=+2)
        # delete_attempt("Kyenshak1")

        # === Show final result ===
        print_all_attempts()