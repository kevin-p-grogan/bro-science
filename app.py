import os
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy

from src.workout_generator import generate_workout

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

from model import *


@app.route('/', methods=['GET', 'POST'])
def index():
    errors = []
    exercises = []
    if request.method == "POST":
        try:
            exercises = generate_workout(request.form['workout_button'], request.form['week'])
        except:
            errors.append(
                "Unable to produce workout."
            )
    return render_template('index.html', errors=errors, exercises=exercises)


if __name__ == '__main__':
    app.run()
