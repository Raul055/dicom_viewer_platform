from dicom_viewer import db, login_manager
from flask_login import UserMixin

# -- Login loader
@login_manager.user_loader
def load_user(user_id):
    # Looks for patient
    user = Patient.query.get(int(user_id))
    if user:
        return user # Patient selected
    # Looks for medic
    return Medic.query.get(int(user_id))

# -- Intermediate table for (N:M) relationship
access_table = db.Table('access_table',
    db.Column('medic_id', db.Integer, db.ForeignKey('medic.id'), primary_key=True),
    db.Column('patient_id', db.Integer, db.ForeignKey('patient.id'), primary_key=True)
)

# -- Patient class (database)
class Patient(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    user_type = db.Column(db.String(10), nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    dicom_image = db.relationship('Dicom_image', backref='patient', lazy=True)

    def __repr__(self):
        return f"User('{self.username}', '{self.user_type}')"

# -- Medic class (database)
class Medic(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    user_type = db.Column(db.String(10), nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    patients = db.relationship('Patient', secondary=access_table, backref='doctors')

    def __repr__(self):
        return f"Medic('{self.username}', '{self.user_type}')"

# -- DICOM class (database)
class Dicom_image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text(), nullable=False)
    image_file = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)

    def __repr__(self):
        return f"DICOM('{self.name}', '{self.image_file}')"