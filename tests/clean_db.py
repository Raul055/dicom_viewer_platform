from dicom_viewer import app, db

with app.app_context():
    # Deletes data and all entries
    db.drop_all()
    # Recreates the db tables (empty)
    db.create_all()
    print("Database cleared and structure rebuilt.")