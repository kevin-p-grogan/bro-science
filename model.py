from app import db


# Create an association table for the many-to-many relationship
exercise_equipment = db.Table(
    'exercise_equipment',
    # use two primary keys as unique identifiers. This act to route the associations.
    db.Column('equipment_name', db.Integer, db.ForeignKey('equipment.name'), primary_key=True),
    db.Column('exercise_name', db.Integer, db.ForeignKey('exercise.name'), primary_key=True)
)


class Exercise(db.Model):
    name = db.Column(db.String(), primary_key=True)
    rating = db.Column(db.Integer)

    # many-to-many relationship
    equipment = db.relationship(
        'Equipment',
        secondary=exercise_equipment,
        backref=db.backref('exercises')
    )

    # many-to-one relationship
    category = db.Column(db.String, db.ForeignKey('category.name'), nullable=False)
    category_relationship = db.relationship("Category", back_populates="exercise_relationship")

    def __repr__(self):
        return '<name:{}>'.format(self.name)


class Equipment(db.Model):
    name = db.Column(db.String(), primary_key=True)

    def __repr__(self):
        return '<name:{}>'.format(self.name)


class Category(db.Model):
    name = db.Column(db.String(), primary_key=True)
    push = db.Column(db.Boolean)  # exercise is a push movement, o.t.w. pull or conditioning
    upper = db.Column(db.Boolean)  # exercise is an upper body exercise, o.t.w. lower or conditioning
    conditioning = db.Column(db.Boolean)  # conditioning exercise; o.t.w. (push, pull) x (upper, lower)

    exercise_relationship = db.relationship('Exercise', back_populates='category_relationship')

    def __repr__(self):
        return '<name:{}>'.format(self.name)