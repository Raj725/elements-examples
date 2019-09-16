from flask import jsonify, make_response
from flask import render_template, url_for, flash, redirect, request
from api import app, stripe
from api.models import Payment


@app.route("/")
def home():
    return render_template('order-form.html')


@app.route('/order', methods=['POST'])
def place_order():
    name = request.form['name']
    email = request.form['email']
    instructions = request.form['instructions']
    payment_info = request.form['paymentInfo']
    payment = Payment(name=name, email=email, instructions=instructions)
    payment.save()
    return jsonify({'datails': payment.name})


@app.route('/payments', methods=['GET'])
def get_active_payments():
    active_payments = Payment.query.all()
    return jsonify({'active_payments': active_payments})


@app.route('/payments/<id>', methods=['POST'])
def process_payment():
    active_payments = Payment.query.all()
    return jsonify({'active_payments': active_payments})
