import secrets
import os
import io
import base64
import numpy as np
from PIL import Image
from flask import render_template, flash, redirect, url_for, request, jsonify, send_from_directory, abort
from dicom_viewer import app, db, bcrypt
from dicom_viewer.forms import login_form, registration_form, update_account_form, DicomUploadForm
from dicom_viewer.models import User, Patient, Medic, Dicom_image, AccessRequest
from flask_login import login_user, current_user, logout_user, login_required
import pydicom

DICOM_UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'dicom_uploads')
os.makedirs(DICOM_UPLOAD_FOLDER, exist_ok=True)

# ── DICOM helpers ──────────────────────────────────────────────────────────────

def dicom_to_png_base64(ds, window_center=None, window_width=None, frame=0):
    if hasattr(ds, 'NumberOfFrames') and int(ds.NumberOfFrames) > 1:
        pixel_array = ds.pixel_array[frame]
    else:
        pixel_array = ds.pixel_array

    if hasattr(ds, 'RescaleSlope') and hasattr(ds, 'RescaleIntercept'):
        pixel_array = pixel_array * float(ds.RescaleSlope) + float(ds.RescaleIntercept)

    if window_center is None or window_width is None:
        if hasattr(ds, 'WindowCenter') and hasattr(ds, 'WindowWidth'):
            wc = ds.WindowCenter
            ww = ds.WindowWidth
            window_center = float(wc[0]) if hasattr(wc, '__iter__') and not isinstance(wc, str) else float(wc)
            window_width  = float(ww[0]) if hasattr(ww, '__iter__') and not isinstance(ww, str) else float(ww)
        else:
            window_center = float(np.median(pixel_array))
            window_width  = float(pixel_array.max() - pixel_array.min()) or 1.0

    low  = window_center - window_width / 2
    high = window_center + window_width / 2
    img  = np.clip(pixel_array, low, high)
    img  = ((img - low) / (high - low) * 255).astype(np.uint8)

    pil_img = Image.fromarray(img)
    if pil_img.mode != 'RGB':
        pil_img = pil_img.convert('RGB')

    buf = io.BytesIO()
    pil_img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode('utf-8')


def extract_metadata(ds):
    tags = [
        ('Patient Name',       str(ds.PatientName)        if hasattr(ds, 'PatientName')        else 'N/A'),
        ('Patient ID',         str(ds.PatientID)          if hasattr(ds, 'PatientID')          else 'N/A'),
        ('Patient Birth Date', str(ds.PatientBirthDate)   if hasattr(ds, 'PatientBirthDate')   else 'N/A'),
        ('Patient Sex',        str(ds.PatientSex)         if hasattr(ds, 'PatientSex')         else 'N/A'),
        ('Study Date',         str(ds.StudyDate)          if hasattr(ds, 'StudyDate')          else 'N/A'),
        ('Study Description',  str(ds.StudyDescription)   if hasattr(ds, 'StudyDescription')   else 'N/A'),
        ('Modality',           str(ds.Modality)           if hasattr(ds, 'Modality')           else 'N/A'),
        ('Manufacturer',       str(ds.Manufacturer)       if hasattr(ds, 'Manufacturer')       else 'N/A'),
        ('Institution',        str(ds.InstitutionName)    if hasattr(ds, 'InstitutionName')    else 'N/A'),
        ('Series Description', str(ds.SeriesDescription)  if hasattr(ds, 'SeriesDescription')  else 'N/A'),
        ('Slice Thickness',    str(ds.SliceThickness)     if hasattr(ds, 'SliceThickness')     else 'N/A'),
        ('Pixel Spacing',      str(ds.PixelSpacing)       if hasattr(ds, 'PixelSpacing')       else 'N/A'),
        ('Rows',               str(ds.Rows)               if hasattr(ds, 'Rows')               else 'N/A'),
        ('Columns',            str(ds.Columns)            if hasattr(ds, 'Columns')            else 'N/A'),
        ('Bits Allocated',     str(ds.BitsAllocated)      if hasattr(ds, 'BitsAllocated')      else 'N/A'),
        ('Window Center',      str(ds.WindowCenter)       if hasattr(ds, 'WindowCenter')       else 'N/A'),
        ('Window Width',       str(ds.WindowWidth)        if hasattr(ds, 'WindowWidth')        else 'N/A'),
        ('Number of Frames',   str(ds.NumberOfFrames)     if hasattr(ds, 'NumberOfFrames')     else '1'),
    ]
    return tags

# ── Standard routes ────────────────────────────────────────────────────────────

@app.route('/')
@app.route('/home')
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
            # Creates row in USER and PATIENT
            user = Patient(
                username=form.username.data,
                email=form.email.data,
                gender=form.gender.data,
                age=form.age.data,
                user_type='Patient', # User type
                password=hashed_password
            )
        elif form.user_type.data == "Medic":
            # Creates row in USER and MEDIC
            user = Medic(
                username=form.username.data,
                email=form.email.data,
                gender=form.gender.data,
                age=form.age.data,
                user_type='Medic', # User type
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
    return render_template('account.html', title='account', image_file=image_file, form=form)

# ── Patient: scans ─────────────────────────────────────────────────────────────

@app.route('/my-scans')
@login_required
def my_scans():
    if current_user.user_type != 'Patient':
        flash('Access restricted to patients.', 'warning')
        return redirect(url_for('home'))
    patient = Patient.query.get(current_user.id)
    scans = patient.dicom_images
    return render_template('my_scans.html', title='My DICOM Scans', scans=scans)

@app.route('/upload-scan', methods=['GET', 'POST'])
@login_required
def upload_scan():
    if current_user.user_type != 'Patient':
        flash('Only patients can upload DICOM scans.', 'warning')
        return redirect(url_for('home'))
    form = DicomUploadForm()
    if form.validate_on_submit():
        f = form.dicom_file.data
        random_hex = secrets.token_hex(10)
        _, ext = os.path.splitext(f.filename)
        filename = random_hex + (ext if ext else '.dcm')
        filepath = os.path.join(DICOM_UPLOAD_FOLDER, filename)
        f.save(filepath)
        try:
            pydicom.dcmread(filepath)
        except Exception:
            os.remove(filepath)
            flash('Invalid DICOM file. Please upload a valid .dcm file.', 'danger')
            return redirect(url_for('upload_scan'))
        scan = Dicom_image(name=form.name.data, description=form.description.data,
                           image_file=filename, patient_id=current_user.id)
        db.session.add(scan)
        db.session.commit()
        flash('DICOM scan uploaded successfully!', 'success')
        return redirect(url_for('my_scans'))
    return render_template('upload_scan.html', title='Upload Scan', form=form)

@app.route('/delete-scan/<int:scan_id>', methods=['POST'])
@login_required
def delete_scan(scan_id):
    scan = Dicom_image.query.get_or_404(scan_id)
    if scan.patient_id != current_user.id:
        abort(403)
    filepath = os.path.join(DICOM_UPLOAD_FOLDER, scan.image_file)
    if os.path.exists(filepath):
        os.remove(filepath)
    db.session.delete(scan)
    db.session.commit()
    flash('Scan deleted.', 'success')
    return redirect(url_for('my_scans'))

# ── Patient: access requests inbox ────────────────────────────────────────────

@app.route('/my-requests')
@login_required
def my_requests():
    if current_user.user_type != 'Patient':
        flash('Access restricted to patients.', 'warning')
        return redirect(url_for('home'))
    patient = Patient.query.get(current_user.id)
    pending   = [r for r in patient.access_requests if r.status == 'pending']
    responded = [r for r in patient.access_requests if r.status != 'pending']
    return render_template('my_requests.html', title='Access Requests',
                           pending=pending, responded=responded)

@app.route('/respond-request/<int:request_id>/<action>', methods=['POST'])
@login_required
def respond_request(request_id, action):
    if current_user.user_type != 'Patient':
        abort(403)
    req = AccessRequest.query.get_or_404(request_id)
    if req.patient_id != current_user.id:
        abort(403)
    if req.status != 'pending':
        flash('This request has already been responded to.', 'warning')
        return redirect(url_for('my_requests'))

    if action == 'approve':
        req.status = 'approved'
        # Link medic <-> patient in the access_table
        medic   = Medic.query.get(req.medic_id)
        patient = Patient.query.get(current_user.id)
        if patient not in medic.patients:
            medic.patients.append(patient)
        db.session.commit()
        flash(f'You have granted Dr. {req.medic.username} access to your scans.', 'success')
    elif action == 'reject':
        req.status = 'rejected'
        db.session.commit()
        flash(f'You have rejected the request from Dr. {req.medic.username}.', 'info')
    else:
        abort(400)

    return redirect(url_for('my_requests'))

@app.route('/revoke-access/<int:medic_id>', methods=['POST'])
@login_required
def revoke_access(medic_id):
    if current_user.user_type != 'Patient':
        abort(403)
    medic   = Medic.query.get_or_404(medic_id)
    patient = Patient.query.get(current_user.id)
    if patient in medic.patients:
        medic.patients.remove(patient)
    # Also mark the related approved request as rejected
    req = AccessRequest.query.filter_by(
        medic_id=medic_id, patient_id=current_user.id, status='approved').first()
    if req:
        req.status = 'rejected'
    db.session.commit()
    flash(f'Access revoked for Dr. {medic.username}.', 'info')
    return redirect(url_for('my_requests'))

# ── Medic: patient list (approved only) & request flow ────────────────────────

@app.route('/patients')
@login_required
def patient_list():
    if current_user.user_type != 'Medic':
        flash('Access restricted to medics.', 'warning')
        return redirect(url_for('home'))
    medic = Medic.query.get(current_user.id)

    # All patients + annotate with request state for this medic
    all_patients = Patient.query.all()
    approved_ids = {p.id for p in medic.patients}

    sent_requests = {r.patient_id: r for r in medic.sent_requests}

    patients_info = []
    for p in all_patients:
        if p.id in approved_ids:
            state = 'approved'
        elif p.id in sent_requests:
            state = sent_requests[p.id].status   # 'pending' or 'rejected'
        else:
            state = 'none'
        patients_info.append({'patient': p, 'state': state})

    return render_template('patient_list.html', title='Patient List',
                           patients_info=patients_info)

@app.route('/request-access/<int:patient_id>', methods=['POST'])
@login_required
def request_access(patient_id):
    if current_user.user_type != 'Medic':
        abort(403)
    patient = Patient.query.get_or_404(patient_id)
    medic   = Medic.query.get(current_user.id)

    # Don't duplicate pending requests
    existing = AccessRequest.query.filter_by(
        medic_id=current_user.id, patient_id=patient_id).first()
    if existing:
        if existing.status == 'pending':
            flash('You already have a pending request for this patient.', 'warning')
        elif existing.status == 'approved':
            flash('You already have access to this patient.', 'info')
        elif existing.status == 'rejected':
            # Allow re-requesting after rejection
            existing.status = 'pending'
            db.session.commit()
            flash(f'Access re-requested from {patient.username}.', 'success')
        return redirect(url_for('patient_list'))

    req = AccessRequest(medic_id=current_user.id, patient_id=patient_id)
    db.session.add(req)
    db.session.commit()
    flash(f'Access requested from patient {patient.username}. Awaiting their approval.', 'success')
    return redirect(url_for('patient_list'))

@app.route('/my-access-requests')
@login_required
def my_sent_requests():
    if current_user.user_type != 'Medic':
        abort(403)
    medic = Medic.query.get(current_user.id)
    return render_template('sent_requests.html', title='My Access Requests',
                           requests=medic.sent_requests)

@app.route('/patient/<int:patient_id>/scans')
@login_required
def patient_scans(patient_id):
    if current_user.user_type != 'Medic':
        flash('Access restricted to medics.', 'warning')
        return redirect(url_for('home'))
    medic   = Medic.query.get(current_user.id)
    patient = Patient.query.get_or_404(patient_id)
    # Enforce access control
    if patient not in medic.patients:
        flash('You do not have access to this patient\'s scans. Request access first.', 'danger')
        return redirect(url_for('patient_list'))
    return render_template('patient_scans.html', title=f"{patient.username}'s Scans",
                           patient=patient, scans=patient.dicom_images)

# ── Shared: viewer ─────────────────────────────────────────────────────────────

@app.route('/view-scan/<int:scan_id>')
@login_required
def view_scan(scan_id):
    scan = Dicom_image.query.get_or_404(scan_id)
    if current_user.user_type == 'Patient':
        if scan.patient_id != current_user.id:
            abort(403)
    elif current_user.user_type == 'Medic':
        medic   = Medic.query.get(current_user.id)
        patient = Patient.query.get(scan.patient_id)
        if patient not in medic.patients:
            abort(403)
    return render_template('viewer.html', title=f'Viewing: {scan.name}', scan=scan)

# ── DICOM API ──────────────────────────────────────────────────────────────────

@app.route('/api/dicom/load/<int:scan_id>')
@login_required
def api_dicom_load(scan_id):
    scan = Dicom_image.query.get_or_404(scan_id)
    if current_user.user_type == 'Patient' and scan.patient_id != current_user.id:
        return jsonify({'error': 'Forbidden'}), 403
    if current_user.user_type == 'Medic':
        medic   = Medic.query.get(current_user.id)
        patient = Patient.query.get(scan.patient_id)
        if patient not in medic.patients:
            return jsonify({'error': 'Forbidden'}), 403

    filepath = os.path.join(DICOM_UPLOAD_FOLDER, scan.image_file)
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found on disk'}), 404

    try:
        ds = pydicom.dcmread(filepath)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    num_frames = int(ds.NumberOfFrames) if hasattr(ds, 'NumberOfFrames') else 1
    metadata   = extract_metadata(ds)
    wc = ww = None
    if hasattr(ds, 'WindowCenter') and hasattr(ds, 'WindowWidth'):
        wc_raw = ds.WindowCenter
        ww_raw = ds.WindowWidth
        wc = float(wc_raw[0]) if hasattr(wc_raw, '__iter__') and not isinstance(wc_raw, str) else float(wc_raw)
        ww = float(ww_raw[0]) if hasattr(ww_raw, '__iter__') and not isinstance(ww_raw, str) else float(ww_raw)

    image_b64 = dicom_to_png_base64(ds, wc, ww, frame=0)
    return jsonify({'scan_id': scan_id, 'filename': scan.image_file,
                    'num_frames': num_frames, 'metadata': metadata,
                    'image': image_b64, 'window_center': wc, 'window_width': ww})

@app.route('/api/dicom/frame', methods=['POST'])
@login_required
def api_dicom_frame():
    data    = request.json
    scan_id = data.get('scan_id')
    frame   = int(data.get('frame', 0))
    wc      = data.get('window_center')
    ww      = data.get('window_width')

    scan = Dicom_image.query.get_or_404(scan_id)
    if current_user.user_type == 'Patient' and scan.patient_id != current_user.id:
        return jsonify({'error': 'Forbidden'}), 403
    if current_user.user_type == 'Medic':
        medic   = Medic.query.get(current_user.id)
        patient = Patient.query.get(scan.patient_id)
        if patient not in medic.patients:
            return jsonify({'error': 'Forbidden'}), 403

    filepath = os.path.join(DICOM_UPLOAD_FOLDER, scan.image_file)
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404

    ds        = pydicom.dcmread(filepath)
    image_b64 = dicom_to_png_base64(ds, wc, ww, frame=frame)
    return jsonify({'image': image_b64})

@app.route('/api/dicom/download/<int:scan_id>')
@login_required
def api_dicom_download(scan_id):
    scan = Dicom_image.query.get_or_404(scan_id)
    if current_user.user_type == 'Patient' and scan.patient_id != current_user.id:
        abort(403)
    if current_user.user_type == 'Medic':
        medic   = Medic.query.get(current_user.id)
        patient = Patient.query.get(scan.patient_id)
        if patient not in medic.patients:
            abort(403)
    return send_from_directory(DICOM_UPLOAD_FOLDER, scan.image_file,
                               as_attachment=True,
                               download_name=scan.name + '.dcm')
