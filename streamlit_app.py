import streamlit as st
from datetime import datetime
import io
from PIL import Image, ImageOps
import numpy as np

# Simple Student Attendance prototype in Streamlit (simulated)
st.set_page_config(page_title='Student Attendance Prototype', layout='centered')

if 'step' not in st.session_state:
    st.session_state.step = 'login'
    st.session_state.user = None
    st.session_state.pin = ''
    st.session_state.barcode = ''
    st.session_state.qr = ''
    st.session_state.attendance = []

def reset_all():
    st.session_state.step = 'login'
    st.session_state.user = None
    st.session_state.pin = ''
    st.session_state.barcode = ''
    st.session_state.qr = ''
    st.session_state.attendance = []

st.title('Student Attendance — Streamlit Prototype')
st.write('Prototype: simulated barcode/QR/face-match flow. Replace simulation with real libraries for production.')

cols = st.columns([1,3,1])
with cols[1]:
    st.write('**Steps:**')
    steps = ['login','applock','scan_barcode','scan_qr','face_match','done']
    for s in steps:
        label = 'App Lock' if s=='applock' else s.replace('_',' ').title()
        if st.session_state.step == s:
            st.markdown(f"<div style='background:#6366f1;color:white;padding:6px;border-radius:8px;margin-bottom:6px'>{label}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='background:#eef2ff;color:#1f2937;padding:6px;border-radius:8px;margin-bottom:6px'>{label}</div>", unsafe_allow_html=True)

# -------------------------
# Normal steps (unchanged)
# -------------------------
if st.session_state.step == 'login':
    st.subheader('Student Login')
    name = st.text_input('Full name', key='name_input')
    college_id = st.text_input('College ID', key='cid_input')
    col1, col2 = st.columns(2)
    if col1.button('Login & Continue'):
        if not name or not college_id:
            st.warning('Enter both name and college ID')
        else:
            st.session_state.user = {'name': name, 'college_id': college_id}
            st.session_state.step = 'applock'
    if col2.button('Reset'):
        reset_all()

elif st.session_state.step == 'applock':
    st.subheader('App Lock (PIN)')
    st.write('Set a 4-digit PIN to secure the app on this device (simulated).')
    pin = st.text_input('Enter 4-digit PIN', type='password', max_chars=4, key='pin_input')
    col1, col2 = st.columns([1,1])
    if col1.button('Set PIN & Continue'):
        if not pin or len(pin) < 4:
            st.warning('Choose a 4-digit PIN')
        else:
            st.session_state.pin = pin
            st.session_state.step = 'scan_barcode'
    if col2.button('Back to Login'):
        st.session_state.step = 'login'

elif st.session_state.step == 'scan_barcode':
    st.subheader('Step 1 — Scan Barcode (College ID)')
    st.write('Simulated: paste/type the barcode string (or your college id)')
    barcode = st.text_input('Barcode value', value=st.session_state.barcode, key='barcode_input')
    col1, col2 = st.columns([1,1])
    if col1.button('Simulate Scan'):
        if not barcode:
            st.warning('Enter barcode string to simulate scanning')
        else:
            st.session_state.barcode = barcode
            st.session_state.step = 'scan_qr'
    if col2.button('Back'):
        st.session_state.step = 'applock'

elif st.session_state.step == 'scan_qr':
    st.subheader('Step 2 — Scan QR shown by teacher')
    st.write('Simulated: paste/type the session id or QR string shown by teacher')
    qr = st.text_input('QR / Session id', value=st.session_state.qr, key='qr_input')
    col1, col2 = st.columns([1,1])
    if col1.button('Simulate QR Scan'):
        if not qr:
            st.warning('Enter QR/session value')
        else:
            st.session_state.qr = qr
            st.session_state.step = 'face_match'
    if col2.button('Back'):
        st.session_state.step = 'scan_barcode'

# -------------------------
# FACE MATCH SECTION (Option 2: camera/upload + compare to repo image)
# -------------------------
elif st.session_state.step == 'face_match':
    st.subheader('Step 3 — Face detection / match')
    st.write('Use your camera or upload a selfie. The app will compare with the student reference photo (if available) or use a demo image.')

    # left: camera/upload, right: reference image
    col1, col2 = st.columns(2)

    with col1:
        st.caption("Capture from camera (recommended) or upload an image")
        cam_img = st.camera_input("Take a selfie")  # works in most modern browsers
        uploaded = st.file_uploader("Or upload a selfie (png/jpg)", type=['png','jpg','jpeg'])
        chosen_image_file = None
        if cam_img is not None:
            chosen_image_file = cam_img
        elif uploaded is not None:
            chosen_image_file = uploaded

    with col2:
        st.write('Student record (reference)')
        if st.session_state.user:
            st.write(f"**{st.session_state.user['name']}**")
            st.write(f"ID: {st.session_state.user['college_id']}")
        st.write(f"Barcode: {st.session_state.barcode}  |  QR: {st.session_state.qr}")

        # reference image path in repo: images/<college_id>.jpg (or .png)
        # demo reference path: images/_demo_student.jpg
        ref_bytes = None
        ref_exists = False
        demo_ref_bytes = None
        try:
            # try jpg then png
            pid = st.session_state.user['college_id']
            for ext in ('.jpg', '.jpeg', '.png'):
                path = f"images/{pid}{ext}"
                try:
                    with open(path, "rb") as f:
                        ref_bytes = f.read()
                        ref_exists = True
                        break
                except FileNotFoundError:
                    continue
        except Exception:
            ref_exists = False

        # load demo image if available
        try:
            with open("images/_demo_student.jpg", "rb") as f:
                demo_ref_bytes = f.read()
        except Exception:
            demo_ref_bytes = None

        if ref_exists:
            st.image(ref_bytes, caption="Reference photo", use_column_width=True)
        else:
            st.info("No reference photo found for this student in images/. Add images/<college_id>.jpg to enable realistic matching.")
            if demo_ref_bytes:
                st.image(demo_ref_bytes, caption="Demo reference (used by Demo Match)", use_column_width=True)
            else:
                st.write("(No demo reference found)")

    st.write("---")

    # helper: compute mean squared error (MSE) between two images (bytes), resized to same size
    def image_mse_bytes(img_bytes_a, img_bytes_b, size=(160,160)):
        try:
            a = Image.open(io.BytesIO(img_bytes_a)).convert("L")
            b = Image.open(io.BytesIO(img_bytes_b)).convert("L")
            a = ImageOps.fit(a, size, Image.Resampling.LANCZOS)
            b = ImageOps.fit(b, size, Image.Resampling.LANCZOS)
            arr_a = np.asarray(a).astype(np.float32) / 255.0
            arr_b = np.asarray(b).astype(np.float32) / 255.0
            mse = np.mean((arr_a - arr_b) ** 2)
            return float(mse)
        except Exception:
            return None

    # Actions & logic
    matched = False
    match_result_text = None

    if chosen_image_file is not None:
        try:
            chosen_bytes = chosen_image_file.getvalue()
        except Exception:
            # streamlit's UploadedFile and camera_input behave similarly
            chosen_bytes = None

        if chosen_bytes is None:
            st.error("Could not read the captured/uploaded image.")
        else:
            # If a real reference exists, compare against it
            if ref_exists and ref_bytes is not None:
                mse = image_mse_bytes(chosen_bytes, ref_bytes)
                if mse is None:
                    st.error("Could not compare images — ensure valid image files.")
                else:
                    threshold = 0.015  # tune as needed
                    if mse <= threshold:
                        matched = True
                        match_result_text = f"Face matched (MSE={mse:.5f}) — attendance granted."
                    else:
                        matched = False
                        match_result_text = f"Face did not match (MSE={mse:.5f}) — attendance denied."
            else:
                st.warning("No student reference photo found. Use 'Demo Match' to show the flow.")
                st.image(chosen_bytes, caption="Captured / Uploaded selfie", use_column_width=True)

        # if we have a textual result, show it and act
        if match_result_text:
            if matched:
                st.success(match_result_text)
                entry = {
                    'name': st.session_state.user['name'],
                    'college_id': st.session_state.user['college_id'],
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'barcode': st.session_state.barcode,
                    'qr': st.session_state.qr,
                }
                st.session_state.attendance.insert(0, entry)
                st.session_state.step = 'done'
            else:
                st.error(match_result_text)

    # Demo match button: uses demo image (or ref if present) to simulate a match for the demo
    if st.button("Demo: Simulate Match (works without local reference)"):
        # pick demo reference if present; else use actual ref if present
        demo_source = None
        if demo_ref_bytes:
            demo_source = demo_ref_bytes
        elif ref_exists and ref_bytes:
            demo_source = ref_bytes

        if demo_source is None:
            st.error("No demo reference image found. Add images/_demo_student.jpg to repo to enable Demo Match.")
        else:
            # If user didn't capture/upload, we simulate capture by using demo_source as chosen_bytes
            if chosen_image_file is None:
                chosen_bytes = demo_source
            else:
                try:
                    chosen_bytes = chosen_image_file.getvalue()
                except Exception:
                    chosen_bytes = demo_source

            mse = image_mse_bytes(chosen_bytes, demo_source)
            if mse is None:
                st.error("Could not compare images.")
            else:
                st.success(f"Demo match succeeded (MSE={mse:.5f}) — attendance granted.")
                entry = {
                    'name': st.session_state.user['name'],
                    'college_id': st.session_state.user['college_id'],
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'barcode': st.session_state.barcode,
                    'qr': st.session_state.qr,
                }
                st.session_state.attendance.insert(0, entry)
                st.session_state.step = 'done'

    if st.button("Back to QR Scan"):
        st.session_state.step = 'scan_qr'

# -------------------------
# DONE page
# -------------------------
elif st.session_state.step == 'done':
    st.subheader('Attendance Recorded ✅')
    latest = st.session_state.attendance[0] if st.session_state.attendance else None
    if latest:
        st.write(f"**{latest['name']}** — {latest['college_id']}")
        st.write(f"Time: {latest['time']}")
        st.write(f"Barcode: {latest['barcode']} | QR: {latest['qr']}")
    col1, col2 = st.columns(2)
    if col1.button('Scan Again'):
        st.session_state.step = 'scan_barcode'
    if col2.button('Logout'):
        reset_all()

# Sidebar attendance log
st.sidebar.title('Attendance Log')
if st.session_state.attendance:
    for a in st.session_state.attendance:
        st.sidebar.write(f"**{a['name']}** — {a['college_id']}")
        st.sidebar.write(a['time'])
        st.sidebar.markdown('---')
else:
    st.sidebar.write('No entries yet.')
