from app import db


# Create an association table for the many-to-many relationship
exercise_equipment = db.Table(
    'exercise_equipment',
    # use two primary keys as unique identifiers. This act to route the associations.
    db.Column('equipment_id', db.Integer, db.ForeignKey('equipment.id'), primary_key=True),
    db.Column('exercise_id', db.Integer, db.ForeignKey('exercise.id'), primary_key=True)
)


class Exercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    rating = db.Column(db.Integer)

    # one-to-many relationship
    variations = db.relationship('Variation', backref=db.backref('exercise'))

    # many-to-many relationship
    equipment = db.relationship(
        'Equipment',
        secondary=exercise_equipment,
        backref=db.backref('exercises')
    )

    # many-to-one relationship
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)

    def __repr__(self):
        return '<id:{}, name:{}>'.format(self.id, self.name)


class Variation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercise.id'), nullable=False)


class Equipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    is_push = db.Column(db.Boolean)  # exercise is a push movement, o.t.w. pull or conditioning
    is_upper = db.Column(db.Boolean)  # exercise is an upper body exercise, o.t.w. lower or conditioning
    is_conditioning = db.Column(db.Boolean)  # conditioning exercise; o.t.w. (push, pull) x (upper, lower)