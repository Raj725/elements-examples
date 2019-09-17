import os

from bson.objectid import ObjectId
from flask import render_template, url_for, redirect, request
from pymongo import MongoClient

from api import app, stripe, STRIPE_PUB_KEY

mongodb_host = os.environ.get('MONGO_HOST', 'localhost')
mongodb_port = int(os.environ.get('MONGO_PORT', '27017'))
client = MongoClient(mongodb_host, mongodb_port)  # Configure the connection to the database
db = client.widgetsOrders  # Select the database
payments_collection = db.payments  # Select the collection


def accept_payment(payment_id):
    payment = payments_collection.find_one({"_id": ObjectId(payment_id)})
    try:
        charge = stripe.Charge.create(
            customer=payment['customer_id'],
            amount=int(float(payment['amount']) * 100),
            currency='usd',
            description='Widget Order'
        )
        payment['status'] = 'accepted'
    except stripe.error.CardError as e:
        # Since it's a decline, stripe.error.CardError will be caught
        body = e.json_body
        err = body.get('error', {})
        print("Status is: %s" % e.http_status)
        print("Type is: %s" % err.get('type'))
        print("Code is: %s" % err.get('code'))
        print("Param is: %s" % err.get('param'))
        print("Message is: %s" % err.get('message'))
        payment['status'] = 'failed'
    except stripe.error.RateLimitError as e:
        # Too many requests made to the API too quickly
        print("Too many requests made to the API too quickly")
        payment['status'] = 'failed'
    except stripe.error.InvalidRequestError as e:
        print("Invalid parameters were supplied to Stripe's API")
        payment['status'] = 'failed'
    except stripe.error.AuthenticationError as e:
        print("Authentication with Stripe's API failed (maybe you changed API keys recently)")
        payment['status'] = 'failed'
    except stripe.error.APIConnectionError as e:
        print("Network communication with Stripe failed")
        payment['status'] = 'failed'
    except stripe.error.StripeError as e:
        print("Display a very generic error to the user, and maybe send yourself an email")
        payment['status'] = 'failed'
    except Exception as e:
        print("Something else happened, completely unrelated to Stripe")
        payment['status'] = 'failed'
        print(e)
    payments_collection.save(payment)


@app.route("/")
def home():
    amount = 100.0
    return render_template('order-form.html', pub_key=STRIPE_PUB_KEY, amount=amount)


@app.route('/order', methods=['POST'])
def place_order():
    # Adding a Payment
    name = request.form['name']
    email = request.form['email']
    instructions = request.form['instructions']
    stripe_token = request.form['stripeToken']
    amount = request.form['amount']
    customer = stripe.Customer.create(email=email, source=stripe_token)
    payments_collection.insert(
        {"name": name, "email": email, "instructions": instructions, "stripeToken": stripe_token, "amount": amount,
         "status": "active", "customer_id": customer.id})
    return render_template('thank_you.html', title="Thank You!")


@app.route('/payments', methods=['GET'])
def get_active_payments():
    active_payments = payments_collection.find({"status": "active"})
    return render_template('payments.html', payments=active_payments)


@app.route('/cancel/<payment_id>')
def cancel_payment(payment_id):
    payments_collection.update({"_id": ObjectId(payment_id)}, {"$set": {"status": "cancelled"}})
    return redirect(url_for('get_active_payments'))


@app.route('/accept/<payment_id>', methods=['POST'])
def take_payment(payment_id):
    accept_payment(payment_id)
    return redirect(url_for('get_active_payments'))


@app.route('/process_payment/<payment_id>', methods=['POST'])
def process_payment(payment_id):
    if request.form['action'] == 'Cancel Payment':
        payments_collection.update({"_id": ObjectId(payment_id)}, {"$set": {"status": "cancelled"}})
    elif request.form['action'] == 'Take Payment':
        accept_payment(payment_id)
    return redirect(url_for('get_active_payments'))
