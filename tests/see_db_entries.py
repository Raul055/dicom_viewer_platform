from dicom_viewer import app, db
from dicom_viewer.models import User, Patient, Medic, Dicom_image

with app.app_context():
    print("\n--- ALL USERS (Base Table) ---")
    users = User.query.all()
    for u in users:
        print(f"ID: {u.id} | Username: {u.username} | Type: {u.user_type} | Email: {u.email}")

    print("\n--- PATIENTS (Specific Table) ---")
    patients = Patient.query.all()
    for p in patients:
        # p has access to User fields AND Patient fields
        print(f"ID: {p.id} | Name: {p.username} | Age: {p.age} | Scans: {len(p.dicom_images)}")

    print("\n--- MEDICS (Specific Table) ---")
    medics = Medic.query.all()
    for m in medics:
        print(f"ID: {m.id} | Dr. {m.username} | Patients Assigned: {len(m.patients)}")

    print("\n--- DICOM IMAGES ---")
    images = Dicom_image.query.all()
    for img in images:
        print(f"ID: {img.id} | Name: {img.name} | Patient: {img.patient.username}")
    print("\n")