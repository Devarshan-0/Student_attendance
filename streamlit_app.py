# streamlit_app.py (cleaned - no demo instructions/messages)
import streamlit as st
from datetime import datetime, timedelta
import io
from PIL import Image, ImageOps
import numpy as np
import secrets
import qrcode
from io import BytesIO

# ---------------------------
# Config / initial session
# ---------------------------
st.set_page_config(page_title='Student Attendance Prototype', layout='centered')

# read session token from URL if present and store in session_state
qp = st.query_params
if 'session' in qp:
    # st.query_params returns lists for values; use first element
    val = qp['session']
    if isinstance(val, list) and len(val) > 0:
        st.session_state.current_session = val[0]
    else:
        st.session_state.current_session = val

if 'step' not in st.session_state:
    st.session_state.step = 'login'
    st.session_state.user = None
    st.session_state.pin = ''
    st.session_state.barcode = ''
    st.session_state.qr = ''
    st.session_state.attendance = []
    st.session_state.current_session = st.session_state.get('current_session', None)
    st.session_state.session_expires = None  # timestamp or None

def reset_all():
    st.session_state.step = 'login'
    st.session_state.user = None
    st.session_state.pin = ''
    st.session_state.barcode = ''
    st.session_state.qr = ''
    st.session_state.attendance = []
    st.session_state.current_session = None
    st.session_state.session_expires = None

# ---------------------------
# Sidebar: Teacher / Admin
# ---------------------------
st.sidebar.title("Teacher / Admin")

# simple checkbox to reveal teacher controls
show_admin = st.sidebar.checkbox("Show teacher panel")

if show_admin:
    st.sidebar.markdown("#### Session controls")
    session_valid_minutes = st.sidebar.number_input("Session valid (minutes)", min_value=5, max_value=240, value=60)
    if st.sidebar.button("Create new session"):
        token = secrets.token_urlsafe(6)
        st.session_state.current_session = token
        st.session_state.session_expires = datetime.now() + timedelta(minutes=int(session_valid_minutes))
        st.sidebar.success(f"Created session: {token} (valid {session_valid_minutes} min)")

    if st.session_state.get('current_session'):
        token = st.session_state.current_session
        expires = st.session_state.session_expires
        if expires and datetime.now() > expires:
            st.sidebar.warning("Current session has expired.")
        st.sidebar.write("**Current session token:**")
        st.sidebar.code(token)
        if expires:
            st.sidebar.write("Expires:", expires.strftime("%Y-%m-%d %H:%M:%S"))
        base = st.sidebar.text_input("App base URL (for QR)", value="https://share.streamlit.io/<your-username>/<repo>/main/streamlit_app.py")
        student_url = f"{base}?session={token}"
        st.sidebar.write("Student URL (scan this QR):")
        st.sidebar.code(student_url)
        qr = qrcode.make(student_url)
        buf = BytesIO()
        qr.save(buf, format="PNG")
        buf.seek(0)
        st.sidebar.image(buf, caption="Scan to join session", use_container_width=True)

        if st.sidebar.button("Expire current session"):
            st.session_state.current_session = None
            st.session_state.session_expires = None
            st.sidebar.info("Session expired.")

# ---------------------------
# Top area: steps display
# ---------------------------
st.title('Student Attendance — Streamlit Prototype')
st.write('Prototype: simulated barcode/QR/face-match flow. Teacher can create session QR in the sidebar.')

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

# ---------------------------
# Helper: simple image similarity (MSE)
# ---------------------------
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

# ---------------------------
# Flow: Login -> AppLock -> ScanBarcode -> ScanQR (skippable by URL) -> FaceMatch -> Done
# ---------------------------
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
    st.write('Simulated: paste/type the barcode string (or your college id). Students can scan teacher QR (session) instead of typing.')
    barcode = st.text_input('Barcode value', value=st.session_state.barcode, key='barcode_input')
    col1, col2 = st.columns([1,1])
    if col1.button('Simulate Scan'):
        if not barcode:
            st.warning('Enter barcode string to simulate scanning')
        else:
            st.session_state.barcode = barcode
            if st.session_state.get('current_session'):
                st.session_state.step = 'face_match'
            else:
                st.session_state.step = 'scan_qr'
    if col2.button('Back'):
        st.session_state.step = 'applock'

elif st.session_state.step == 'scan_qr':
    st.subheader('Step 2 — Scan QR shown by teacher')
    st.write('If you opened the app by scanning the teacher QR, this step is skipped automatically.')
    current_session = st.session_state.get('current_session')
    if current_session:
        st.success(f"Joined session: {current_session}")
        if st.button("Continue to face-match"):
            st.session_state.step = 'face_match'
    else:
        st.write("No session detected. If teacher has shown a session QR, open the app via that QR. Otherwise simulate by entering a session code.")
        qr = st.text_input('Session / QR value', value=st.session_state.qr, key='qr_input')
        col1, col2 = st.columns([1,1])
        if col1.button('Use this session'):
            if not qr:
                st.warning('Enter QR/session value')
            else:
                st.session_state.qr = qr
                st.session_state.current_session = qr
                st.session_state.step = 'face_match'
        if col2.button('Back'):
            st.session_state.step = 'scan_barcode'

# ---------------------------
# Face match (camera/upload + image-similarity demo)
# ---------------------------
elif st.session_state.step == 'face_match':
    st.subheader('Step 3 — Face detection / match')
    st.write('Use your camera or upload a selfie. The app compares with the student reference photo (if present) or use Demo Match.')

    col1, col2 = st.columns(2)
    with col1:
        st.caption("Capture from camera (recommended) or upload an image")
        cam_img = st.camera_input("Take a selfie")
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
        st.write(f"Barcode: {st.session_state.barcode}  |  Session: {st.session_state.get('current_session')}")

        # try to load reference image from images/<college_id>.(jpg|png)
        ref_bytes = None
        ref_exists = False
        demo_ref_bytes = None
        try:
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

        try:
            with open("_demo_student.jpg", "rb") as f:
                demo_ref_bytes = f.read()
        except Exception:
            demo_ref_bytes = None

        if ref_exists:
            st.image(ref_bytes, caption="Reference photo", use_container_width=True)
        else:
            # intentionally quiet: no instructional messages shown here
            if demo_ref_bytes:
                st.image(demo_ref_bytes, caption="Demo reference (used by Demo Match)", use_container_width=True)

    st.write("---")

    # Comparison & actions
    if chosen_image_file is not None:
        try:
            chosen_bytes = chosen_image_file.getvalue()
        except Exception:
            chosen_bytes = None

        if chosen_bytes is None:
            st.error("Could not read the captured/uploaded image.")
        else:
            if ref_exists and ref_bytes:
                mse = image_mse_bytes(chosen_bytes, ref_bytes)
                if mse is None:
                    st.error("Could not compare images — ensure valid image files.")
                else:
                    threshold = 0.015
                    if mse <= threshold:
                        st.success(f"Face matched (MSE={mse:.5f}) — attendance granted.")
                        entry = {
                            'name': st.session_state.user['name'],
                            'college_id': st.session_state.user['college_id'],
                            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'barcode': st.session_state.barcode,
                            'session': st.session_state.get('current_session')
                        }
                        st.session_state.attendance.insert(0, entry)
                        st.session_state.step = 'done'
                    else:
                        st.error(f"Face did not match (MSE={mse:.5f}) — attendance denied.")
            else:
                # quiet when no reference; show captured image only
                st.image(chosen_bytes, caption="Captured / Uploaded selfie", use_container_width=True)

    if st.button("Demo: Simulate Match (works without local reference)"):
        demo_source = demo_ref_bytes if demo_ref_bytes else ref_bytes
        if demo_source is None:
            st.error("No demo reference available.")
        else:
            chosen_bytes = None
            if 'chosen_image_file' in locals() and chosen_image_file is not None:
                try:
                    chosen_bytes = chosen_image_file.getvalue()
                except Exception:
                    chosen_bytes = demo_source
            if chosen_bytes is None:
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
                    'session': st.session_state.get('current_session')
                }
                st.session_state.attendance.insert(0, entry)
                st.session_state.step = 'done'

    if st.button("Back to QR / Session"):
        st.session_state.step = 'scan_qr'

# ---------------------------
# Done page
# ---------------------------
elif st.session_state.step == 'done':
    st.subheader('Attendance Recorded ✅')
    latest = st.session_state.attendance[0] if st.session_state.attendance else None
    if latest:
        st.write(f"**{latest['name']}** — {latest['college_id']}")
        st.write(f"Time: {latest['time']}")
        st.write(f"Barcode: {latest.get('barcode','')} | Session: {latest.get('session','')}")
    col1, col2 = st.columns(2)
    if col1.button('Scan Again'):
        st.session_state.step = 'scan_barcode'
    if col2.button('Logout'):
        reset_all()

# ---------------------------
# Sidebar: attendance log
# ---------------------------
st.sidebar.title('Attendance Log')
if st.session_state.attendance:
    for a in st.session_state.attendance:
        st.sidebar.write(f"**{a['name']}** — {a['college_id']}")
        st.sidebar.write(a['time'])
        st.sidebar.write(f"Session: {a.get('session','')}")
        st.sidebar.markdown('---')
else:
    st.sidebar.write('No entries yet.')
