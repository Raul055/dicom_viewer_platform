from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, NumberRange, ValidationError
from dicom_viewer.models import User
from flask_login import current_user

# Registration form class
# -- Used for database parameters
class registration_form(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    gender = SelectField('Gender', choices=[('Male', 'Male'),
                                            ('Female', 'Female'),
                                            ('Other', 'Other')], 
                      validators=[DataRequired()])
    age = IntegerField('Age', 
                       validators=[DataRequired(), NumberRange(min=1, max=120)])
    user_type = SelectField('User Type', choices=[('Patient', 'Patient'),
                                                  ('Medic', 'Medic')], 
                      validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    # Check if username is already taken
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()

        if user:
            raise ValidationError('Username already taken. Please select another one.')

    # Check if email is already taken
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        
        if user:
            raise ValidationError('Email already taken. Please select another one.')

# Registration form class
# -- Used for database parameters
class login_form(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Login')

# Update account form class
# -- Used for database parameters
class update_account_form(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    picture = FileField('Update Profile Picture',
                            validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')

    # Check if username is already taken
    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Username already taken. Please select another one.')

    # Check if email is already taken
    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Email already taken. Please select another one.')