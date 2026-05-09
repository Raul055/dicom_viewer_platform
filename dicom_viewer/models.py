from dicom_viewer import db

access_table = db.Table('access_table',
    db.Column('medic_id', db.Integer, db.ForeignKey('medic.id'), primary_key=True),
    db.Column('patient_id', db.Integer, db.ForeignKey('patient.id'), primary_key=True)
)

class Patient(db.Model):
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

class Medic(db.Model):
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

class Dicom_image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text(), nullable=False)
    image_file = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)


    def __repr__(self):
        return f"DICOM('{self.name}', '{self.image_file}')"