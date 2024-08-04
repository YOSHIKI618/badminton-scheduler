from app import db

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    grade = db.Column(db.Integer, nullable=False)
    level = db.Column(db.Integer, nullable=False)
    participation = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Player {self.name}>'
