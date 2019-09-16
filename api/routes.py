import datetime
import uuid

import jwt
from flask import jsonify, make_response
from flask import render_template, url_for, flash, redirect, request
from flask_login import current_user
from werkzeug.security import generate_password_hash, check_password_hash

from api import app, db, PROCESSED_DIR
from api.forms import UploadImageForm
from api.models import ApiRequest, User, Todo
from api.utils import process_and_get_measures, token_required


# from measurement_result import get_measurements


@app.route("/", methods=['GET', 'POST'])
def upload():
    form = UploadImageForm()
    if form.validate_on_submit():
        # Read form data
        side_img = form.side_img.data
        front_img = form.front_img.data
        height = form.height.data
        # Process and Get Measures
        measure = process_and_get_measures(side_img, front_img, height)
        return redirect(url_for('results', measure_id=measure.id))
    return render_template('upload.html', form=form, title='Upload Images')


@app.route("/upload", methods=['GET', 'POST'])
def upload_file():
    # checking if the parameters are present or not.
    if 'side_img' not in request.files:
        return "No side_img file found"
    if 'front_img' not in request.files:
        return "No front_img file found"
    if 'height' not in request.form:
        return "No height found in the request"

    # Read form data
    side_img = request.files['side_img']
    front_img = request.files['front_img']
    height = request.form['height']
    # Process and Get Measures
    measure = process_and_get_measures(side_img, front_img, height)
    result = {
        'side_img': measure.side_img,
        'front_img': measure.front_img,
        'height': measure.height,
        'measures': measure.measures
    }
    return result


@app.route("/result/<int:measure_id>")
def results(measure_id):
    measure = ApiRequest.query.get_or_404(measure_id)
    return render_template('result.html', measure=measure, processed_dir=PROCESSED_DIR)


@app.route("/dashboard")
def home():
    # measures = ApiRequest.query.order_by(ApiRequest.id.desc()).all()
    measures = ApiRequest.query.order_by(ApiRequest.id).all()
    return render_template('home.html', measures=measures, processed_dir=PROCESSED_DIR)


@app.route("/about")
def about():
    response = {'content': 'This program uses the refined silhouette and pose information to calculate body slices'}
    content_type = request.headers.get('Content-Type')
    if content_type is not None and content_type == 'application/json':
        return jsonify(response)
    return render_template('about.html', title='About')


@app.route('/user', methods=['GET'])
@token_required
def get_all_users(current_user):
    if not current_user.admin:
        return jsonify({'message': 'Cannot perform that function!'})

    users = User.query.all()

    output = []

    for user in users:
        user_data = {}
        user_data['email'] = user.public_id
        user_data['name'] = user.name
        user_data['password'] = user.password
        user_data['admin'] = user.admin
        output.append(user_data)

    return jsonify({'users': output})


@app.route('/user/<email>', methods=['GET'])
@token_required
def get_one_user(current_user, public_id):
    if not current_user.admin:
        return jsonify({'message': 'Cannot perform that function!'})

    user = User.query.filter_by(public_id=public_id).first()

    if not user:
        return jsonify({'message': 'No user found!'})

    user_data = {}
    user_data['email'] = user.public_id
    user_data['name'] = user.name
    user_data['password'] = user.password
    user_data['admin'] = user.admin

    return jsonify({'user': user_data})


@app.route('/user', methods=['POST'])
@token_required
def create_user(current_user):
    if not current_user.admin:
        return jsonify({'message': 'Cannot perform that function!'})

    data = request.get_json()

    hashed_password = generate_password_hash(data['password'], method='sha256')

    new_user = User(public_id=str(uuid.uuid4()), name=data['name'], password=hashed_password, admin=False)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'New user created!'})


@app.route('/user/activate/<email>', methods=['PUT'])
@token_required
def activate_user_account(current_user, public_id):
    if not current_user.admin:
        return jsonify({'message': 'Cannot perform that function!'})

    user = User.query.filter_by(public_id=public_id).first()

    if not user:
        return jsonify({'message': 'No user found!'})

    user.admin = True
    db.session.commit()

    return jsonify({'message': 'The user has been promoted!'})


@app.route('/user/<email>', methods=['PUT'])
@token_required
def promote_user(current_user, public_id):
    if not current_user.admin:
        return jsonify({'message': 'Cannot perform that function!'})

    user = User.query.filter_by(public_id=public_id).first()

    if not user:
        return jsonify({'message': 'No user found!'})

    user.admin = True
    db.session.commit()

    return jsonify({'message': 'The user has been promoted!'})


@app.route('/user/<email>', methods=['DELETE'])
@token_required
def delete_user(current_user, public_id):
    if not current_user.admin:
        return jsonify({'message': 'Cannot perform that function!'})

    user = User.query.filter_by(public_id=public_id).first()

    if not user:
        return jsonify({'message': 'No user found!'})

    db.session.delete(user)
    db.session.commit()

    return jsonify({'message': 'The user has been deleted!'})


@app.route('/login')
def login():
    auth = request.authorization

    if not auth or not auth.username or not auth.password:
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})

    user = User.query.filter_by(name=auth.username).first()

    if not user:
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})

    if check_password_hash(user.password, auth.password):
        token = jwt.encode(
            {'email': user.public_id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)},
            app.config['SECRET_KEY'])

        return jsonify({'token': token.decode('UTF-8')})

    return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})


@app.route('/todo', methods=['GET'])
@token_required
def get_all_todos(current_user):
    todos = Todo.query.filter_by(user_id=current_user.id).all()

    output = []

    for todo in todos:
        todo_data = {}
        todo_data['id'] = todo.id
        todo_data['text'] = todo.text
        todo_data['complete'] = todo.complete
        output.append(todo_data)

    return jsonify({'todos': output})


@app.route('/todo/<todo_id>', methods=['GET'])
@token_required
def get_one_todo(current_user, todo_id):
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id).first()

    if not todo:
        return jsonify({'message': 'No todo found!'})

    todo_data = {}
    todo_data['id'] = todo.id
    todo_data['text'] = todo.text
    todo_data['complete'] = todo.complete

    return jsonify(todo_data)


@app.route('/todo', methods=['POST'])
@token_required
def create_todo(current_user):
    data = request.get_json()

    new_todo = Todo(text=data['text'], complete=False, user_id=current_user.id)
    db.session.add(new_todo)
    db.session.commit()

    return jsonify({'message': "Todo created!"})


@app.route('/todo/<todo_id>', methods=['PUT'])
@token_required
def complete_todo(current_user, todo_id):
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id).first()

    if not todo:
        return jsonify({'message': 'No todo found!'})

    todo.complete = True
    db.session.commit()

    return jsonify({'message': 'Todo item has been completed!'})


@app.route('/todo/<todo_id>', methods=['DELETE'])
@token_required
def delete_todo(current_user, todo_id):
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id).first()

    if not todo:
        return jsonify({'message': 'No todo found!'})

    db.session.delete(todo)
    db.session.commit()

    return jsonify({'message': 'Todo item deleted!'})


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)
