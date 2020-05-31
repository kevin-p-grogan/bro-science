import pandas as pd
import yaml
from collections import Iterable
from copy import deepcopy

from src.excercise_database import EXCERCISE_DATAFRAME

FILTERS_FILENAME = 'data/filters.yaml'
WORKOUTS_FILENAME = 'data/workouts.yaml'
KEYWORD = 'inherit'


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
        if k == KEYWORD:
            inherited = deepcopy(root[workouts[k]])
            merged_workouts = __deep_merge_dictionaries(inherited, workouts)

    for k, v in merged_workouts.items():
        if k == KEYWORD:
            del workouts[k]
        else:
            workouts[k] = v


def __load_workout(workout_name):
    # load the raw workout
    with open(WORKOUTS_FILENAME, 'r') as workouts_file:
        workouts = yaml.load(workouts_file)
        __resolve_inheritance(workouts, workouts)
        return workouts[workout_name]


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
        df = df.sample(n=1, weights=df.rating)
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


def generate_workout(workout_name, week):
    exercise_dataframe = pd.read_pickle(EXCERCISE_DATAFRAME)
    exercise_dataframe = __apply_filters(exercise_dataframe)
    full_workout_name = ' '.join((workout_name, week))
    workout = __load_workout(full_workout_name)
    exercises = __select_exercises(workout, exercise_dataframe)
    return __convert_to_template(exercises)
