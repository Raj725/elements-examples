from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from api.config import STRIPE_SECRET_KEY, STRIPE_PUB_KEY

import stripe

app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

stripe.api_key = STRIPE_SECRET_KEY



# Initialize database and perform migrations
db = SQLAlchemy(app)
db.init_app(app)
migrate = Migrate(app, db)


# Create all database tables
@app.before_first_request
def create_tables():
    db.create_all()


from api import routes
