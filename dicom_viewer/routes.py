import secrets
import os
from PIL import Image
from flask import render_template, flash, redirect, url_for, request
from dicom_viewer import app, db, bcrypt
from dicom_viewer.forms import login_form, registration_form, update_account_form
from dicom_viewer.models import User, Patient, Medic
from flask_login import login_user, current_user, logout_user, login_required

# -- Home route
@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html')

# -- Register route
@app.route("/register", methods=['GET', 'POST'])
def register():
    # User is already authenticated
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = registration_form()

    # Check if submit is valid
    if form.validate_on_submit():
        # Password is hashed
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        
        # Inside your register route logic
        if form.user_type.data == "Patient":
            # This automatically creates a row in 'user' AND 'patient'
            user = Patient(
                username=form.username.data,
                email=form.email.data,
                gender=form.gender.data,
                age=form.age.data,
                user_type='Patient', # Sets polymorphic_identity
                password=hashed_password
            )
        elif form.user_type.data == "Medic":
            # This automatically creates a row in 'user' AND 'medic'
            user = Medic(
                username=form.username.data,
                email=form.email.data,
                gender=form.gender.data,
                age=form.age.data,
                user_type='Medic', # Sets polymorphic_identity
                password=hashed_password
            )
        # Adds info to database
        db.session.add(user)
        db.session.commit()
        flash(f'Your account as {form.user_type.data} was created!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

# -- Login route
@app.route("/login", methods=['GET', 'POST'])
def login():
    # User is already authenticated
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = login_form()

    # Check if login is valid
    if form.validate_on_submit():
        # Checks if user is in db to do a login
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

# -- Logout route
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

# -- Save profile picture into profile_pics directory
def save_picture(form_picture):
    # Gives a random hex to image and builds path
    random_hex = secrets.token_hex(8)
    _, file_extention = os.path.splitext(form_picture.filename)
    picture_file_name = random_hex + file_extention
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_file_name)
    
    # Rezise image to 125x125
    output_size = (125,125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)

    # Saves resized image
    i.save(picture_path)
    return picture_file_name

# -- Account route
@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = update_account_form()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='account',
                           image_file=image_file, form=form)