from dicom_viewer import app, db
from dicom_viewer.models import User, Patient, Medic
from sqlalchemy import inspect

with app.app_context():
    # List all tables in the db
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"Tables found in DB: {tables}")

    # Check if core tables exist
    required = ['user', 'patient', 'medic']
    if all(t in tables for t in required):
        print("Success: Inheritance tables are present.")
    else:
        missing = [t for t in required if t not in tables]
        print(f"Missing tables: {missing}")
        print("Try running db.create_all() after deleting the old .db file.")

    # Test inheritance (foreign key)
    try:
        # Creates test patient
        test_p = Patient(
            username="TestUser", 
            email="test@test.com", 
            password="pass",
            gender="Other",
            age=0,
            user_type="Patient"
        )
        db.session.add(test_p)
        db.session.commit()
        
        # Verify if exists in User
        user_entry = User.query.filter_by(username="TestUser").first()
        print(f"Inheritance Test: Created Patient ID {test_p.id}. Found in User table as ID {user_entry.id}.")
        
        # Clean up
        db.session.delete(test_p)
        db.session.commit()
    except Exception as e:
        print(f"Logic Error: {e}")