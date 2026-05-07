from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email

class registration_form(FlaskForm):
    username = StringField('Username',
                            validators=[DataRequired(), Length(max=20)])
    email = StringField('Email',
                            validators=[DataRequired(), Email()])
    password = PasswordField('Password', validator=[DataRequired()])

class login_form(FlaskForm):
    username = StringField('Username',
                            validators=[DataRequired(), Length(max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Login')
