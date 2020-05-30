import random

#from src.excercise_database import create_exercise_database


def generate_workout(workout_type, week):
    exercise_database = create_exercise_database()
    week = (week-1) % 4 + 1
    exercises = list()

    if workout_type in ["Upper Push", "Upper Pull", "Lower Push", "Lower Pull"]:
        group, primary_direction = workout_type.lower().split()
        secondary_direction = "push" if primary_direction == "pull" else "pull"
        exercises.append({
            'Type': 'Primary',
            'Exercise': select_exercise(exercise_database, 'primary', group, primary_direction, week),
            'Sets and Reps': get_sets_and_reps('primary', group, primary_direction, week)
        })
        exercises.append({
            'Type': 'Secondary',
            'Exercise': select_exercise(exercise_database, 'secondary', group, secondary_direction, week),
            'Sets and Reps': get_sets_and_reps('secondary', group, secondary_direction, week)
        })
        exercises.append({
            'Type': 'Circuit',
            'Exercise': select_exercise(exercise_database, 'assistance', group, primary_direction, week),
            'Sets and Reps': get_sets_and_reps('assistance', group, primary_direction, week)
        })
        exercises.append({
            'Type': 'Circuit',
            'Exercise': select_exercise(exercise_database, 'assistance', group, secondary_direction, week),
            'Sets and Reps': get_sets_and_reps('assistance', group, secondary_direction, week)
        })
        exercises.append({
            'Type': 'Circuit',
            'Exercise': select_exercise(exercise_database, 'core', 'core', 'core', week),
            'Sets and Reps': get_sets_and_reps('assistance', 'core', 'core', week)
        })
        exercises.append({
            'Type': 'Burner',
            'Exercise': select_exercise(exercise_database, 'accessory', group, primary_direction, week),
            'Sets and Reps': get_sets_and_reps('accessory', group, primary_direction, week)
        })
        exercises.append({
            'Type': 'Burner',
            'Exercise': select_exercise(exercise_database, 'accessory', group, secondary_direction, week),
            'Sets and Reps': get_sets_and_reps('accessory', group, secondary_direction, week)
        })

    return exercises


def select_exercise(exercises, category, group, direction, week):
        exercise_priorities = {ex: exercises[ex]['priority'] *
                                 (10 if (ex.split(' ')[-1] == 'bands') and\
                                         (week == 1) and
                                         (category ==' primary')\
                                         else 1)
                              for ex in exercises
                              if (exercises[ex]['category'] == category) and
                                 (exercises[ex]['group'] == group) and
                                 (exercises[ex]['direction'] == direction)}
        weighted_list = []
        for ex in exercise_priorities: weighted_list += exercise_priorities[ex]*[ex]
        selected_exercise = random.choice(weighted_list)
        del exercises[selected_exercise]
        return selected_exercise


def get_sets_and_reps(category, group, direction, week):
    if category == 'primary':
        if group =='lower' and direction == 'pull':
            if week == 1:
                sets = "10"
                reps = "1"
            elif week == 2:
                sets = "1"
                reps = "5"
            elif week == 3:
                sets = "1"
                reps = "3"
            else:
                sets = "1x"
                reps = "1"

        else:
            if week == 1:
                sets = "8"
                reps = "3"
            elif week == 2:
                sets = "3"
                reps = "5"
            elif week == 3:
                sets = "3"
                reps = "3"
            else:
                sets = "1"
                reps = "1"

    elif category == 'secondary':
        sets = '4'
        reps = '6-10'

    elif category == 'accessory':
        sets = '1'
        reps = '40-60'

    else:
        sets = '3'
        reps = '8-15'

    return f"{sets}x{reps}"
