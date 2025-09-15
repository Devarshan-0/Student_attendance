# streamlit_app.py
import streamlit as st
from datetime import datetime, timedelta
import io, secrets
from PIL import Image, ImageOps
import numpy as np
import qrcode
from io import BytesIO

# ---------------------------
# App config
# ---------------------------
st.set_page_config(page_title='Student Attendance Prototype', layout='centered')

# read session token from URL
qp = st.query_params
if 'session' in qp:
    val = qp['session']
    if isinstance(val, list) and len(val) > 0:
        st.session_state.current_session = val[0]
    else:
        st.session_state.current_session = val

# initialize session state
if 'step' not in st.session_state:
    st.session_state.step = 'login'
    st.session_state.user = None
    st.session_state.pin = ''
    st.session_state.barcode = ''
    st.session_state.qr = ''
    st.session_state.attendance = []
    st.session_state.current_session = st.session_state.get('current_session', None)
    st.session_state.session_expires = None

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
# Sidebar: teacher/admin (session QR generator)
# ---------------------------
st.sidebar.title("Teacher / Admin")
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
# Top UI (steps)
# ---------------------------
st.title('Student Attendance — Streamlit Prototype')
st.write('Fast demo: simulated app-lock + camera-based barcode/QR scanning (or use Fake Scan).')

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
# Helper: image similarity (MSE)
# ---------------------------
def image_mse_bytes(a_bytes, b_bytes, size=(160,160)):
    try:
        a = Image.open(io.BytesIO(a_bytes)).convert("L")
        b = Image.open(io.BytesIO(b_bytes)).convert("L")
        a = ImageOps.fit(a, size, Image.Resampling.LANCZOS)
        b = ImageOps.fit(b, size, Image.Resampling.LANCZOS)
        arr_a = np.asarray(a).astype(np.float32) / 255.0
        arr_b = np.asarray(b).astype(np.float32) / 255.0
        return float(np.mean((arr_a - arr_b) ** 2))
    except Exception:
        return None

# small helper to generate a fake scanned code string
def mk_fake_code(prefix='SCN'):
    return f"{prefix}-{secrets.token_urlsafe(4)}"

# ---------------------------
# Step: LOGIN
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

# ---------------------------
# Step: APP LOCK (PIN + Simulated fingerprint)
# ---------------------------
elif st.session_state.step == 'applock':
    st.subheader('App Lock (PIN or Fingerprint)')
    st.write('You can set a 4-digit PIN OR use the fingerprint button below (simulated biometric). For demo the fingerprint always unlocks.')

    col_a, col_b = st.columns([2,1])
    with col_a:
        pin = st.text_input('Enter 4-digit PIN (optional)', type='password', max_chars=4, key='pin_input')
    with col_b:
        # fingerprint button (simulated biometric) - always succeeds
        if st.button("🔒 Use Fingerprint (Simulated)", key='fingerprint_btn'):
            st.session_state.pin = 'biometric'
            st.session_state.step = 'scan_barcode'

    # if user enters a 4-digit pin and presses Set PIN
    col1, col2 = st.columns([1,1])
    if col1.button('Set PIN & Continue'):
        if not pin or len(pin) < 4:
            st.warning('Choose a 4-digit PIN or use the fingerprint button')
        else:
            st.session_state.pin = pin
            st.session_state.step = 'scan_barcode'
    if col2.button('Back to Login'):
        st.session_state.step = 'login'

# ---------------------------
# Step: SCAN BARCODE (camera-based or Fake)
# ---------------------------
elif st.session_state.step == 'scan_barcode':
    st.subheader('Step 1 — Scan Barcode (College ID)')
    st.write('Point the camera at the college ID barcode and press Capture, OR tap Fake Scan to proceed quickly.')

    # camera capture: any captured image is treated as a successful scan
    cam = st.camera_input("Camera — point at barcode and Capture (any capture will be accepted)")
    col1, col2 = st.columns([1,1])
    if col1.button("Fake Scan (accept anything)"):
        # generate a fake barcode string and continue
        st.session_state.barcode = mk_fake_code('BAR')
        # if session already exists skip QR step
        if st.session_state.get('current_session'):
            st.session_state.step = 'face_match'
        else:
            st.session_state.step = 'scan_qr'

    if cam is not None:
        try:
            # we don't decode the barcode image — accept any non-empty capture
            bytes_data = cam.getvalue()
            # optionally you can compute a hash or any deterministic token:
            st.session_state.barcode = mk_fake_code('BAR')
            if st.session_state.get('current_session'):
                st.session_state.step = 'face_match'
            else:
                st.session_state.step = 'scan_qr'
        except Exception:
            st.error("Could not read camera capture — try Fake Scan.")

    if col2.button("Back"):
        st.session_state.step = 'applock'

# ---------------------------
# Step: SCAN QR (camera-based or Fake)
# ---------------------------
elif st.session_state.step == 'scan_qr':
    st.subheader('Step 2 — Scan Teacher QR (Session)')
    st.write('Point the camera at the teacher\'s QR. Any capture or Fake QR will join the session automatically.')

    cam_q = st.camera_input("Camera — point at teacher QR and Capture (accepted as successful)")
    c1, c2 = st.columns([1,1])
    if c1.button("Fake QR (accept anything)"):
        # create fake session token if none exists
        token = st.session_state.get('current_session') or secrets.token_urlsafe(6)
        st.session_state.current_session = token
        st.session_state.step = 'face_match'

    if cam_q is not None:
        try:
            _ = cam_q.getvalue()
            # accept anything and set a session token (teacher should normally generate)
            token = st.session_state.get('current_session') or secrets.token_urlsafe(6)
            st.session_state.current_session = token
            st.session_state.step = 'face_match'
        except Exception:
            st.error("Could not read camera capture — try Fake QR.")

    if c2.button("Back"):
        st.session_state.step = 'scan_barcode'

# ---------------------------
# Step: FACE MATCH (as before) — unchanged logic but works with prior fake scans
# ---------------------------
elif st.session_state.step == 'face_match':
    st.subheader('Step 3 — Face detection / match')
    st.write('Take a selfie with camera or upload one. For demo you can use Demo Match or an uploaded/captured selfie. Any capture is accepted for the demo flow after matching logic.')

    col1, col2 = st.columns(2)
    with col1:
        cam_img = st.camera_input("Take a selfie")
        uploaded = st.file_uploader("Or upload a selfie (png/jpg)", type=['png','jpg','jpeg'])
        chosen = None
        if cam_img is not None:
            chosen = cam_img
        elif uploaded is not None:
            chosen = uploaded

    with col2:
        st.write('Student record:')
        if st.session_state.user:
            st.write(f"**{st.session_state.user['name']}**")
            st.write(f"ID: {st.session_state.user['college_id']}")
        st.write(f"Barcode: {st.session_state.barcode}  |  Session: {st.session_state.get('current_session')}")

    # try to load reference, but demo will accept captured image if no ref
    ref_bytes = None
    ref_exists = False
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

    demo_ref_bytes = None
    try:
        with open("images/_demo_student.jpg", "rb") as f:
            demo_ref_bytes = f.read()
    except Exception:
        demo_ref_bytes = None

    st.write("---")

    # if any selfie captured, try to compare if reference exists; else accept demo behavior
    if chosen is not None:
        try:
            chosen_bytes = chosen.getvalue()
        except Exception:
            chosen_bytes = None

        if chosen_bytes is None:
            st.error("Could not read the captured/uploaded image.")
        else:
            if ref_exists and ref_bytes:
                mse = image_mse_bytes(chosen_bytes, ref_bytes)
                if mse is None:
                    st.error("Could not compare images.")
                else:
                    threshold = 0.015
                    if mse <= threshold:
                        st.success(f"Face matched (MSE={mse:.5f}) — attendance granted.")
                        st.session_state.attendance.insert(0, {
                            'name': st.session_state.user['name'],
                            'college_id': st.session_state.user['college_id'],
                            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'barcode': st.session_state.barcode,
                            'session': st.session_state.get('current_session')
                        })
                        st.session_state.step = 'done'
                    else:
                        st.error(f"Face did not match (MSE={mse:.5f}) — attendance denied.")
            else:
                # demo: accept any captured selfie as match (fast demo)
                st.success("Demo: selfie captured — attendance granted.")
                st.session_state.attendance.insert(0, {
                    'name': st.session_state.user['name'],
                    'college_id': st.session_state.user['college_id'],
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'barcode': st.session_state.barcode,
                    'session': st.session_state.get('current_session')
                })
                st.session_state.step = 'done'

    # Demo button (also accepts without ref)
    if st.button("Demo: Simulate Match (no reference needed)"):
        st.session_state.attendance.insert(0, {
            'name': st.session_state.user['name'],
            'college_id': st.session_state.user['college_id'],
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'barcode': st.session_state.barcode,
            'session': st.session_state.get('current_session')
        })
        st.session_state.step = 'done'

    if st.button("Back to QR / Session"):
        st.session_state.step = 'scan_qr'

# ---------------------------
# Done
# ---------------------------
elif st.session_state.step == 'done':
    st.subheader('Attendance Recorded ✅')
    latest = st.session_state.attendance[0] if st.session_state.attendance else None
    if latest:
        st.write(f"**{latest['name']}** — {latest['college_id']}")
        st.write(f"Time: {latest['time']}")
        st.write(f"Barcode: {latest.get('barcode','')} | Session: {latest.get('session','')}")
    c1, c2 = st.columns(2)
    if c1.button('Scan Again'):
        st.session_state.step = 'scan_barcode'
    if c2.button('Logout'):
        reset_all()

# ---------------------------
# Sidebar log
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
