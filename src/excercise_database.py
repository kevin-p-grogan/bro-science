from itertools import product
from app import db
from collections import namedtuple
from model import Equipment, Exercise, Category
from copy import deepcopy
import yaml

EXCERCISE_FILENAME = 'data/exercises.yaml'
NAME_MAP = {
    'descriptor': 'name',
    'name': 'primary_name',
    'equipment_categories': ['free weight', 'accomodating resistance', 'other equipment'],
    'rating': 'rating',
    'push': 'push',
    'upper': 'upper',
    'conditioning': 'conditioning'
}
DEFAULTS = {
    'rating': 5,
    'push': True,
    'upper': True,
    'conditioning': False
}

CategoryTuple = namedtuple('CategoryTuple', ['name', 'push', 'upper', 'conditioning'])
ExerciseTuple = namedtuple('ExerciseTuple', ['name', 'rating', 'equipment', 'category'])
EquipmentTuple = namedtuple('EquipmentTuple', ['name'])


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
        name += f' with {equipment.name}'
    elif num_equipments >= 2:
        name += f' with'
        for i, equipment in enumerate(equipments):
            if i == num_equipments - 1:
                name += f' and {equipment.name}'
            else:
                name += f' {equipment.name},'

    return name


def get_equipment(raw_exercise):
    equipment_categories = NAME_MAP['equipment_categories']
    equipments = set()
    for idx, equipment_category in enumerate(equipment_categories):
        equipment = raw_exercise.get(equipment_category, None)
        if equipment is not None:
            equipments.add(EquipmentTuple(name=equipment))
    return equipments


def get_category(raw_exercise):
    push = raw_exercise.get(NAME_MAP['push'], DEFAULTS['push'])
    upper = raw_exercise.get(NAME_MAP['upper'], DEFAULTS['upper'])
    conditioning = raw_exercise.get(NAME_MAP['conditioning'], DEFAULTS['conditioning'])

    direction = 'push' if push else 'pull'
    group = 'upper' if upper else 'lower'
    if conditioning:
        return CategoryTuple(name='conditioning', push=False, upper=False, conditioning=conditioning)
    else:
        return CategoryTuple(name=f'{group} {direction}', push=push, upper=upper, conditioning=conditioning)


def create_database(raw_exercises):

    all_equipments = set()
    all_categories = set()
    all_exercises = set()

    # First create the tuples; these allow for the exercises/categories/equipment to be hashed and stored in a set
    for raw_exercise in raw_exercises:
        equipments = get_equipment(raw_exercise)
        name = create_name(raw_exercise, equipments)
        category = get_category(raw_exercise)

        rating = raw_exercise.get(NAME_MAP['rating'], DEFAULTS['rating'])
        all_exercises.add(ExerciseTuple(name=name, rating=rating, equipment=tuple(equipments), category=category))
        all_categories.add(category)
        all_equipments = all_equipments.union(equipments)

    # Convert the tuples
    all_equipments = [Equipment(**e._asdict()) for e in all_equipments]
    all_categories = [Category(**c._asdict()) for c in all_categories]
    all_exercises = [
        Exercise(
            name=ex.name,
            rating=ex.rating,
            equipment=[e for et, e in product(ex.equipment, all_equipments) if et.name == e.name],
            category=next(c for c in all_categories if ex.category.name == c.name)
        ) for ex in all_exercises
    ]

    # Create the database
    db.rollback()
    db.create_all()
    for ex in all_exercises:
        db.session.add(ex)
    db.session.commit()
    pass


if __name__ == '__main__':
    with open(EXCERCISE_FILENAME, 'r') as exercise_file:
        compressed_exercises = yaml.load(exercise_file)
        raw_exercises = decompress_exercises(compressed_exercises)
        create_database(raw_exercises)

# from itertools import product
# def create_exercise_database():
#     '''gets all the exercises'''
#     exercises = dict()
#     ##########################################################################
#     #make lower push primary
#     vars1 = ['box','free']
#     vars2 = ['straight bar', 'ssb', 'cambered bar', 'Duffalo bar']
#     vars3 = ['with bands','with chains', '']
#     category = "primary"
#     group = "lower"
#     direction = "push"
#     name = "squat"
#     priority = 1
#     for var1, var2, var3 in product(vars1,vars2,vars3):
#         exercise = "{} {} {} {}".format(var1,var2,name,var3)
#         exercises[exercise] = {"priority": priority,
#                         "category": category,
#                         "group": group,
#                         "direction": direction
#                 }
#     ##########################################################################
#     #make lower pull primary
#     vars1 = ['conventional','sumo','snatch grip','trap bar']
#     vars2 = ['deficit','blocks','rack pull']
#     vars3 = ['with bands','with chains','']
#     category = "primary"
#     group = "lower"
#     direction = "pull"
#     name = "deadlift"
#     priority = 1
#     for var1, var2, var3 in product(vars1,vars2,vars3):
#         exercise = "{} {} {} {}".format(var1,var2,name,var3)
#         exercises[exercise] = {"priority": priority,
#                         "category": category,
#                         "group": group,
#                         "direction": direction
#                 }
#     ##########################################################################
#     #make upper push primary
#     vars1 = ['close grip','middle grip','wide grip']
#     vars2 = ['foam', 'football bar', 'Duffalo bar', 'floor', 'floor bridge','']
#     vars3 = ['with bands','with slingshot', 'with chains','']
#     vars4 = ['and fat gripz', '']
#     category = "primary"
#     group = "upper"
#     direction = "push"
#     name = "bench press"
#     priority = 3
#     for var1, var2, var3, var4 in product(vars1,vars2,vars3, vars4):
#         exercise = "{} {} {} {} {}".format(var1,var2,name,var3,var4)
#         if var1=='trap bar' and var2[2:]!='board': var2==''
#         if var2=='floor' and var3=='with slingshot': var3=''
#         exercises[exercise] = {"priority": priority if var2[2:]!='board' else 1,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     ##########################################################################
#     #make upper pull primary
#     #rows
#     vars1 = ['pronated','supinated', 'swiss bar']
#     vars2 = ['Pendlay', 'strict']
#     category = "primary"
#     group = "upper"
#     direction = "pull"
#     name = "barbell row"
#     priority = 1
#     for var1, var2 in product(vars1,vars2):
#         exercise = "{} {} {}".format(var1,var2,name)
#         exercises[exercise] = {"priority": priority,
#                         "category": category,
#                          "group": group,
#                          "direction": direction
#                 }
#     #other
#     vars1 = ['hang clean', 'snatch grip high pull']
#     category = "primary"
#     group = "upper"
#     direction = "pull"
#     name = ""
#     priority = 2
#     for var1 in vars1:
#         exercise = "{} {}".format(var1,name)
#         exercises[exercise] = {"priority": priority,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     ##########################################################################
#     #make the upper push secondary
#     vars1 = ['Anderson','Zercher', 'barbell Hack', 'barbell front', 'cambered bar front']
#     vars2 = ['with chains','with bands', '']
#     category = "secondary"
#     group = "lower"
#     direction = "push"
#     name = "squat"
#     priority = 1
#     for var1, var2 in product(vars1, vars2):
#         exercise = "{} {} {}".format(var1, name, var2)
#         exercises[exercise] = {"priority": priority,
#                         "category": category,
#                          "group": group,
#                          "direction": direction
#                 }
#     ##########################################################################
#     #make lower pull secondary
#     #deadlift
#     vars1 = ['Romanian', 'defecit Romanian','Dimmel', 'seated']
#     category = "secondary"
#     group = "lower"
#     direction = "pull"
#     name = "deadlift"
#     priority = 1
#     for var1 in vars1:
#         exercise = "{} {}".format(var1,name)
#         exercises[exercise] = {"priority": priority,
#                         "category": category,
#                          "group": group,
#                          "direction": direction
#                 }
#     exercises['barbell hipthrust'] = {"priority": 3,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     ##########################################################################
#     #make upper push secondary
#     #dips
#     vars1 = ['chest', 'tricep']
#     category = "secondary"
#     group = "upper"
#     direction = "push"
#     name = "dips"
#     priority = 2
#     for var1 in vars1:
#         exercise = "{} {}".format(var1,name)
#         exercises[exercise] = {"priority": priority,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     #press variations
#     vars1 = ['guillotine', 'Spoto', 'incline',  'shoulder', 'push', 'pin', 'decline']
#     category = "secondary"
#     group = "upper"
#     direction = "push"
#     name = "press"
#     priority = 1
#     for var1 in vars1:
#         exercise = "{} {}".format(var1,name)
#         exercises[exercise] = {"priority": priority,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     ##########################################################################
#     #make the upper pull secondary
#     #chin ups
#     vars1 = ['close grip','middle grip']
#     category = "secondary"
#     group = "upper"
#     direction = "pull"
#     name = "chin up"
#     priority = 1
#     for var1 in vars1:
#         exercise = "{} {}".format(var1,name)
#         exercises[exercise] = {"priority": priority,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     #pull ups
#     vars1 = ['middle grip', 'wide grip']
#     category = "secondary"
#     group = "upper"
#     direction = "pull"
#     name = "pull up"
#     priority = 1
#     for var1 in vars1:
#         exercise = "{} {}".format(var1,name)
#         exercises[exercise] = {"priority": priority,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     #inverted rows
#     vars1 = ['neutral grip', 'supinated grip', 'pronated grip']
#     category = "secondary"
#     group = "upper"
#     direction = "pull"
#     name = "inverted row"
#     priority = 1
#     for var1 in vars1:
#         exercise = "{} {}".format(var1,name)
#         exercises[exercise] = {"priority": priority,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['trap bar shrugs'] = {"priority": 1,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['barbell shrugs'] = {"priority": 1,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['seal row'] = {"priority": 1,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['swiss bar seal row'] = {"priority": 1,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['cambered bar seal row'] = {"priority": 1,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     ##########################################################################
#     #make lower push assistance
#     category = "assistance"
#     group = "lower"
#     direction = "push"
#     exercises['goblet squat'] = {"priority": 4,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['landmine squat'] = {"priority": 4,
#                       "category": category,
#                       "group": group,
#                       "direction": direction
#             }
#     exercises['belt squat'] = {"priority": 4,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['bulgarian split squat'] = {"priority": 3,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#
#     exercises['machine hack squat'] = {"priority": 6,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['plie squat'] = {"priority": 4,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#
#
#     exercises['step ups'] = {"priority": 3,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['leg press'] = {"priority": 4,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     ##########################################################################
#     #make lower push accessory
#     category = "accessory"
#     group = "lower"
#     direction = "push"
#     exercises['x band walks'] = {"priority": 5,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#
#     exercises['banded hip abductor'] = {"priority": 5,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['sissy squats'] = {"priority": 4,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['leg extensions'] = {"priority": 4,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['calf raises'] = {"priority": 3,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     ##########################################################################
#     #make lower pull assistance
#     category = "assistance"
#     group = "lower"
#     direction = "pull"
#     exercises['back raises'] = {"priority": 3,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['single leg deadlift'] = {"priority": 3,
#                       "category": category,
#                       "group": group,
#                       "direction": direction
#             }
#     exercises['45 degree back raises'] = {"priority": 5,
#                       "category": category,
#                       "group": group,
#                       "direction": direction
#             }
#     exercises['banded dumbbell RDL'] = {"priority": 3,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['glute-ham raises'] = {"priority": 5,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#
#     exercises['landmine deadlift'] = {"priority": 4,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['snatch grip barbell hypers'] = {"priority": 2,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     #good morning
#     vars1 = ['', 'banded', 'rack', 'chained', 'ssb', 'seated', 'cambered bar']
#     name = "good morning"
#     priority = 1
#     for var1 in vars1:
#         exercise = "{} {}".format(var1,name)
#         exercises[exercise] = {"priority": priority,
#                         "category": category,
#                          "group": group,
#                          "direction": direction
#                 }
#     ##########################################################################
#     #make lower pull accessory
#     category = "accessory"
#     group = "lower"
#     direction = "pull"
#     exercises['leg curls'] = {"priority": 3,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['single leg hip thrust'] = {"priority": 4,
#                   "category": category,
#                   "group": group,
#                   "direction": direction
#             }
#     exercises['banded pullthrough'] = {"priority": 2,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['cable pullthrough'] = {"priority": 3,
#                       "category": category,
#                       "group": group,
#                       "direction": direction
#             }
#     exercises['kettlebell swing'] = {"priority": 2,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['reverse hypers'] = {"priority": 5,
#                       "category": category,
#                       "group": group,
#                       "direction": direction
#             }
#     ##########################################################################
#     #make upper push assistance
#     category = "assistance"
#     group = "upper"
#     direction = "push"
#     #press variations
#     vars1 = ['dumbbell','one armed']
#     vars2 = ['shoulder', 'incline','bench', 'decline','standing']
#     name = "press"
#     priority = 1
#     for var1, var2 in product(vars1,vars2):
#         if var1 == 'standing' and var2!='shoulder': continue
#         exercise = "{} {} {}".format(var1,var2,name)
#         exercises[exercise] = {"priority": priority,
#                         "category": category,
#                          "group": group,
#                          "direction": direction
#                 }
#
#     #pushup variations
#     vars1 = ['close', 'wide','medium', 'slingshot']
#     name = "pushup"
#     priority = 1
#     for var1 in vars1:
#         exercise = "{} {}".format(var1,name)
#         exercises[exercise] = {"priority": priority,
#                         "category": category,
#                          "group": group,
#                          "direction": direction
#                 }
#
#     exercises['JM Press'] = {"priority": 2,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['chair dips'] = {"priority": 3,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['Z Press'] = {"priority": 4,
#                       "category": category,
#                       "group": group,
#                       "direction": direction
#             }
#
#
#     ##########################################################################
#     #make upper push accessory
#     category = "accessory"
#     group = "upper"
#     direction = "push"
#     exercises['skull crushers'] = {"priority": 2,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['Tricep Kickbacks'] = {"priority": 2,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['Bradford Press'] = {"priority": 3,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['Tate Press'] = {"priority": 3,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['banded tricep extensions'] = {"priority": 2,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['cable tricep extensions'] = {"priority": 3,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['overhead tricep extensions'] = {"priority": 1,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['rolling tricep extensions'] = {"priority": 2,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     #raise variations
#     vars1 = ['front', 'lateral','IYT', 'banded V']
#     name = "raises"
#     priority = 2
#     for var1 in vars1:
#         exercise = "{} {}".format(var1,name)
#         exercises[exercise] = {"priority": priority,
#                         "category": category,
#                          "group": group,
#                          "direction": direction
#                 }
#
#     exercises['dumbbell fly'] = {"priority": 2,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['machine fly'] = {"priority": 4,
#                       "category": category,
#                       "group": group,
#                       "direction": direction
#             }
#     exercises['cable cross overs'] = {"priority": 2,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     ##########################################################################
#     #make upper pull assistance
#     category = "assistance"
#     group = "upper"
#     direction = "pull"
#     #row variations
#     vars1 = ['landmine', 'chest supported', 'cable']
#     name = "row"
#     priority = 2
#     for var1 in vars1:
#         exercise = "{} {}".format(var1,name)
#         exercises[exercise] = {"priority": priority,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#
#     exercises['banded pullups'] = {"priority": 1,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['lat pulldowns'] = {"priority": 5,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['dumbbell row'] = {"priority": 4,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['seated cable facepull'] = {"priority": 5,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     ##########################################################################
#     #make upper pull accessory
#     category = "accessory"
#     group = "upper"
#     direction = "pull"
#
#     exercises['upright row'] = {"priority": 2,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#
#     exercises['standing cable facepull'] = {"priority": 3,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#
#     #bicep curl variations
#     vars1 = ['hammer', 'barbell', 'pinwheel','preacher','cable']
#     vars2 = ['','banded']
#     name = "curl"
#     priority = 1
#     for var1, var2 in product(vars1,vars2):
#         exercise = "{} {} {}".format(var1,var2,name)
#         exercises[exercise] = {"priority": 2*priority if vars2=='banded' else priority,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#
#     ##########################################################################
#     #make core exercises
#     category = group = direction = "core"
#     exercises['hanging knee raises'] = {"priority": 1,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['cable crunches'] = {"priority": 4,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['Russian twists'] = {"priority": 2,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['Excersise ball ab pull-ins'] = {"priority": 2,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['Scissor kicks'] = {"priority": 1,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['side planks'] = {"priority": 1,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['planks'] = {"priority": 2,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['Chinese plank'] = {"priority": 1,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['side bends'] = {"priority": 2,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['around the worlds'] = {"priority": 1,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['lying leg raises'] = {"priority": 2,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['reverse crunch'] = {"priority": 1,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['v situps'] = {"priority": 3,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['mountain climbers'] = {"priority": 1,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['ab rollers'] = {"priority": 2,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['rope crunches'] = {"priority": 4,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['farmers walks'] = {"priority": 6,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['sled push'] = {"priority": 4,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['dumbbell snatch'] = {"priority": 3,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['suitcase carries'] = {"priority": 1,
#                           "category": category,
#                           "group": group,
#                           "direction": direction
#                 }
#     exercises['Roman chair sit ups'] = {"priority": 2,
#                       "category": category,
#                       "group": group,
#                       "direction": direction
#             }
#     exercises['Yoke carries'] = {"priority": 3,
#                       "category": category,
#                       "group": group,
#                       "direction": direction
#             }
#     exercises['death marches'] = {"priority": 2,
#               "category": category,
#               "group": group,
#               "direction": direction
#               }
#     exercises['landmine squat and press'] = {"priority": 3,
#                       "category": category,
#                       "group": group,
#                       "direction": direction
#             }
#
#     return exercises
