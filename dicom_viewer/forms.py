from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, NumberRange

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

class login_form(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Login')
