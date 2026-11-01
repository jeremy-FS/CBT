from flask import Flask, render_template
import json

app = Flask(__name__)

@app.route('/')
def dashboard():
    with open('questions.json', 'r', encoding='utf-8') as f:
        questions = json.load(f)
    return render_template('dashboard.html', questions=questions)

if __name__ == '__main__':
    app.run(host="127.0.0.1", port="8001", debug=True)