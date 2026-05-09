from flask import render_template, flash, redirect, url_for, request
from dicom_viewer import app, db, bcrypt
from dicom_viewer.forms import login_form, registration_form
from dicom_viewer.models import Patient, Medic, Dicom_image
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
        
        # Register was a patient
        if form.user_type.data == "Patient":
            user = Patient(
                username=form.username.data,
                email=form.email.data,
                gender=form.gender.data,
                age=form.age.data,
                user_type=form.user_type.data,
                password=hashed_password
            )
        # Register was a medic
        else:
            user = Medic(
                username=form.username.data,
                email=form.email.data,
                gender=form.gender.data,
                age=form.age.data,
                user_type=form.user_type.data,
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
        # Login for patients
        if form.user_type.data == "Patient":
            # Checks if a patient user exists in database to login
            patient = Patient.query.filter_by(email=form.email.data).first()
            if patient and bcrypt.check_password_hash(patient.password, form.password.data):
                login_user(patient, remember=form.remember_me.data)
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('home'))
        
        # Login for medics
        elif form.user_type.data == "Medic":
            # Checks if a medic user exists in database to login
            medic = Medic.query.filter_by(email=form.email.data).first()
            if medic and bcrypt.check_password_hash(medic.password, form.password.data):
                login_user(medic, remember=form.remember_me.data)
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('home'))
        flash('Login unsuccessful. Check username and password.', 'danger')
    return render_template('login.html', title='Login', form=form)

# -- Logout route
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

# -- Account route
@app.route("/account")
@login_required
def account():
    return render_template('account.html', title='account')