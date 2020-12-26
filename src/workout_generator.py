import pandas as pd
import yaml
from collections import Iterable
from copy import deepcopy
from datetime import datetime
import pickle as pkl
import json

from src.excercise_database import EXCERCISE_DATAFRAME

FILTERS_FILENAME = 'data/filters.yaml'
WORKOUTS_FILENAME = 'data/raw_workouts.yaml'
FULL_WORKOUTS_JSON = 'data/workouts.json'
EXERCISE_CACHE = 'data/exercise_tmp.pkl'

INHERITANCE_KEYWORD = 'inherit'
COMPLETE_WORKOUT_KEYWORD = 'Complete'

def create_workouts_json(filename):
    workouts = load_workouts()
    with open(filename, 'w') as f:
        json.dump(workouts, f, indent=5)


def __deep_merge_dictionaries(a, b, path=None):
    "merges b into a. Adapted from https://stackoverflow.com/questions/7204805/how-to-merge-dictionaries-of-dictionaries/7205107#7205107 "

    if path is None:
        path = []

    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                __deep_merge_dictionaries(a[key], b[key], path + [str(key)])
            else:
                a[key] = b[key]
        else:
            a[key] = b[key]

    return a


def __resolve_inheritance(workouts, root):
    if not isinstance(workouts, dict):
        return

    merged_workouts = workouts
    for k, v in workouts.items():
        __resolve_inheritance(v, root)
        if k == INHERITANCE_KEYWORD:
            inherited = deepcopy(root[workouts[k]])
            merged_workouts = __deep_merge_dictionaries(inherited, workouts)

    for k, v in merged_workouts.items():
        if k == INHERITANCE_KEYWORD:
            del workouts[k]
        else:
            workouts[k] = v


def __load_workout(workout_name):
    # load the raw workout
    workouts = load_workouts()
    return workouts[workout_name]


def load_workouts():
    with open(WORKOUTS_FILENAME, 'r') as workouts_file:
        workouts = yaml.load(workouts_file)
        __resolve_inheritance(workouts, workouts)
        workouts = __filter_partial_workouts(workouts)
    return workouts


def __filter_partial_workouts(workouts):
    filtered_workouts = dict()
    for k, v in workouts.items():
        if v.get(COMPLETE_WORKOUT_KEYWORD, False):
            del v[COMPLETE_WORKOUT_KEYWORD]
            filtered_workouts[k] = v

    return filtered_workouts


def __apply_filters(df):
    df = df.copy()
    with open(FILTERS_FILENAME, 'r') as filters_file:
        filters = yaml.load(filters_file)

        for column, value in filters.items():
            if column in df.columns:
                if not isinstance(value, Iterable):
                    values = [value]
                else:
                    values = value

                keep = df[column].map(
                    lambda v: v in values if not isinstance(v, Iterable) else all(vi in values for vi in v)
                )
                df = df[keep]

    return df


def __select_exercises(workout, exercise_dataframe):
    dfs = []
    for exercise in workout:
        df = exercise_dataframe.copy()
        for column in (c for c in workout[exercise] if c in df.columns and workout[exercise][c] is not None):
            df = df[df[column] == workout[exercise][column]]

        seed = datetime.now().microsecond
        df = df.sample(n=1, weights=df.rating, random_state=seed)
        df['type'] = exercise
        df['sets_and_reps'] = workout[exercise]['sets and reps']
        df['order'] = workout[exercise]['order']
        dfs.append(df)

    df = pd.concat(dfs)
    return df.sort_values(by='order')


def __convert_to_template(exercises):
    template = []
    for _, row in exercises.iterrows():
        template.append({
            'Exercise': row['name'],
            'Type': row.type,
            'Sets and Reps': row.sets_and_reps
        })

    return template


#TODO: Change how the tracking of exercises is handled. This is not scalable to more than one user.
def __load_exercises():
    """Load the temporary file of exercises"""
    with open(EXERCISE_CACHE, 'rb') as f:
        exercises = pkl.load(f)

    return exercises


def __save_exercises(exercises):
    """Save exercises out to temporary file"""
    with open(EXERCISE_CACHE, 'wb') as f:
        pkl.dump(exercises, f)


def resample_exercise(exercise):
    exercises = __load_exercises()
    exercise_dataframe = pd.read_json(EXCERCISE_DATAFRAME)
    exercise_dataframe = __apply_filters(exercise_dataframe)

    old_exercise = exercise_dataframe[exercise_dataframe.name == exercise]
    direction_and_group = old_exercise.direction_and_group.iloc[0]
    category = old_exercise.category.iloc[0]
    df = exercise_dataframe[
        (exercise_dataframe.category == category) & (exercise_dataframe.direction_and_group == direction_and_group)
    ]

    new_exercise = df.sample(n=1, weights=df.rating, random_state=datetime.now().microsecond).name.iloc[0]
    exercises.name[exercises.name == exercise] = new_exercise

    __save_exercises(exercises)
    return __convert_to_template(exercises)


def generate_workout(workout_name, week):
    exercise_dataframe = pd.read_json(EXCERCISE_DATAFRAME)
    exercise_dataframe = __apply_filters(exercise_dataframe)
    full_workout_name = ' '.join((workout_name, week))
    workout = __load_workout(full_workout_name)
    exercises = __select_exercises(workout, exercise_dataframe)
    __save_exercises(exercises)
    return __convert_to_template(exercises)

if __name__ == "__main__":
    #  Generate and save the workout.
    create_workouts_json(FULL_WORKOUTS_JSON)


