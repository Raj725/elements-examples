import stripe
from flask import Flask

from api.config import STRIPE_SECRET_KEY, STRIPE_PUB_KEY, SECRET_KEY

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
stripe.api_key = STRIPE_SECRET_KEY

from api import routes
