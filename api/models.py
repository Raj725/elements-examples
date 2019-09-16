from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from api import db


class CRUD:
    id = None

    def save(self):
        if self.id is None:
            db.session.add(self)
        return db.session.commit()

    def destroy(self):
        db.session.delete(self)
        return db.session.commit()


class User(db.Model, CRUD):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    admin = db.Column(db.Boolean)
    api_key = db.Column(db.String(100))

    api_requests = db.relationship('ApiRequest', backref='user', lazy=True)
    subscription = db.relationship('Subscription', backref='user', lazy=True)
    payments = db.relationship('Payment', backref='user', lazy=True)

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

class ApiRequest(db.Model, CRUD):
    id = db.Column(db.Integer, primary_key=True)
    front_img = db.Column(db.String(100), nullable=True)
    side_img = db.Column(db.String(100), nullable=True)
    height = db.Column(db.Integer, nullable=True)
    measures = db.Column(db.Text(), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    request_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class Subscription(db.Model, CRUD):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    expiry_date = db.Column(db.DateTime, nullable=False)
    plan = db.relationship('Plan', backref='subscriptions', lazy=True)


class Plan(db.Model, CRUD):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    price = db.Column(db.Float)
    validity = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('subscription.id'), nullable=False)


class Payment(db.Model, CRUD):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    amount = db.Column(db.Float)
    status = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class Todo(db.Model, CRUD):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(50))
    complete = db.Column(db.Boolean)
    user_id = db.Column(db.Integer)
