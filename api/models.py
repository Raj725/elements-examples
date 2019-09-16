from datetime import datetime

from api import db


class CRUD:
    id = None
    def save(self):
        if self.id is None:
            db.session.add(self)
        return db.session.commit()

class Payment(db.Model, CRUD):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    instructions = db.Column(db.Text)
    amount = db.Column(db.Float)
    token = db.Column(db.String(100))
    status = db.Column(db.String(100), default='active')
    order_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


