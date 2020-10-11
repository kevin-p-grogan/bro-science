import os
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy


from src.workout_generator import generate_workout, resample_exercise

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
            errors.append("Unable to produce workout.")

    return render_template('index.html', errors=errors, exercises=exercises)


@app.route('/resample', methods=['POST'])
def resample():
    errors = []
    exercises = []
    if request.method == "POST":
        try:
            exercises = resample_exercise(request.form['resample_button'])

        except:
            errors.append(
                "Unable to produce workout."
            )
    return render_template('index.html', errors=errors, exercises=exercises)


@app.route('/generate', methods=['POST'])
def generate():
    req = request.get_json()
    try:
        exercises = generate_workout(req['workout'], req['week'])
        resp = jsonify(exercises)
        resp.status_code = 200
    except Exception as e:
        print(e)
        message = {
            'status': 500,
            'message': "Unable to produce workout.",
        }
        resp = jsonify(message)
        resp.status_code = 500

    return resp


if __name__ == '__main__':
    app.run()
