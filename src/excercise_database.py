from itertools import product
from collections import namedtuple
import pandas as pd
from copy import deepcopy
import yaml

RAW_EXCERCISE_FILENAME = 'data/raw_exercises.yaml'
EXCERCISE_DATAFRAME = 'data/exercises.json'

NAME_MAP = {
    'descriptor': 'name',
    'name': 'primary_name',
    'category': 'category',
    'equipment_categories': ['free weight', 'accomodating resistance', 'other equipment'],
    'rating': 'rating',
    'push': 'push',
    'upper': 'upper',
    'conditioning': 'conditioning'
}
DEFAULTS = {
    'rating': 5,
    'category': 'accessory',
    'push': True,
    'upper': True,
    'conditioning': False
}

Exercise = namedtuple('ExerciseTuple', ['name', 'rating', 'equipment', 'category', 'direction_and_group'])


def _populate_exercises(data, template_exercise, exercises, key):
    """This function recursively populates exercises taken from the raw YAML file."""
    exercise = deepcopy(template_exercise)

    if not isinstance(data, dict):
        exercise[key] = data
        exercises.append(exercise)
    else:
        lists = {}
        for k, v in data.items():
            if isinstance(v, list):
                lists[k] = v
            else:
                exercise[k] = v

        if len(lists) == 0:
            exercises.append(exercise)
        elif len(lists) == 1:  # if there is only one list, just iterate
            k, v = list(lists.items())[0]
            for item in v:
                _populate_exercises(item, exercise, exercises, k)
        else:
            for combo in product(*lists.values()):  # if there are multiple lists, use a product rule to decompress
                new_data = {k: v for k, v in zip(lists.keys(), combo)}
                _populate_exercises(new_data, exercise, exercises, key)


def decompress_exercises(compressed_exercises):
    """This function takes the raw exercises taken in a compressed format extracts the individual exercises"""
    exercises = list()

    for primary_name, data in compressed_exercises.items():
        exercise = {NAME_MAP['name']: primary_name}
        _populate_exercises(data, exercise, exercises, primary_name)

    return exercises


def create_name(raw_exercise, equipments):

    descriptor = raw_exercise.get(NAME_MAP['descriptor'], None)
    name = '{} '.format(descriptor) if descriptor is not None else ''
    name += raw_exercise[NAME_MAP['name']]

    num_equipments = len(equipments)
    if num_equipments == 1:
        equipment = equipments.pop()
        equipments.add(equipment)
        name += f' with {equipment}'
    elif num_equipments >= 2:
        name += f' with'
        for i, equipment in enumerate(equipments):
            if i == num_equipments - 1:
                name += f' and {equipment}'
            else:
                name += f' {equipment},'

    return name


def get_equipment(raw_exercise):
    equipment_categories = NAME_MAP['equipment_categories']
    equipments = set()
    for idx, equipment_category in enumerate(equipment_categories):
        equipment = raw_exercise.get(equipment_category, None)
        if equipment is not None:
            equipments.add(equipment)
    return equipments


def get_direction_and_group(raw_exercise):
    push = raw_exercise.get(NAME_MAP['push'], DEFAULTS['push'])
    upper = raw_exercise.get(NAME_MAP['upper'], DEFAULTS['upper'])
    conditioning = raw_exercise.get(NAME_MAP['conditioning'], DEFAULTS['conditioning'])

    direction = 'push' if push else 'pull'
    group = 'upper' if upper else 'lower'
    if conditioning:
        return 'conditioning'
    else:
        return f'{group} {direction}'


def create_dataframe(raw_exercises):

    exercises = set()

    # First create the tuples; these allow for the exercises to be hashed and stored in a set
    for raw_exercise in raw_exercises:
        equipments = get_equipment(raw_exercise)
        name = create_name(raw_exercise, equipments)
        direction_and_group = get_direction_and_group(raw_exercise)

        rating = raw_exercise.get(NAME_MAP['rating'], DEFAULTS['rating'])
        category = raw_exercise.get(NAME_MAP['category'], DEFAULTS['category'])
        exercises.add(
            Exercise(
                name=name,
                rating=rating,
                equipment=tuple(equipments),
                category=category,
                direction_and_group=direction_and_group)
        )

    return pd.DataFrame(ex._asdict() for ex in exercises)


if __name__ == '__main__':
    with open(RAW_EXCERCISE_FILENAME, 'r') as exercise_file:
        compressed_exercises = yaml.load(exercise_file)
        raw_exercises = decompress_exercises(compressed_exercises)
        df = create_dataframe(raw_exercises)
        df.to_json(EXCERCISE_DATAFRAME, orient="index", indent=5)
