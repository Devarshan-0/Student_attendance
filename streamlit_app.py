# streamlit_app.py
import streamlit as st
from datetime import datetime, timedelta
import io, secrets
from PIL import Image, ImageOps
import numpy as np
import qrcode
from io import BytesIO
import time


# ---------------------------
# App config
# ---------------------------
st.set_page_config(page_title='Student Attendance Prototype', layout='centered')

# read session token from URL (new API)
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
st.write('Demo mode — simulated biometric + camera-driven scanning that auto-advances.')

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
# Helper: small image-similarity (optional)
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
# ---------------------------
# Step: APP LOCK (PIN + nicer simulated fingerprint)
# ---------------------------
elif st.session_state.step == 'applock':
    st.subheader('App Lock (PIN or Fingerprint)')
    st.write('Set a 4-digit PIN or use the fingerprint scanner (simulated). For demo the fingerprint will always unlock.')

    # layout: left = instructions + pin, right = fingerprint UI
    left, right = st.columns([2,1])

    with left:
        pin = st.text_input('Enter 4-digit PIN (optional)', type='password', max_chars=4, key='pin_input')
        row_a, row_b = st.columns([1,1])
        if row_a.button('Set PIN & Continue'):
            if not pin or len(pin) < 4:
                st.warning('Choose a 4-digit PIN or use the fingerprint scanner.')
            else:
                st.session_state.pin = pin
                st.session_state.step = 'scan_barcode'
        if row_b.button('Back to Login'):
            st.session_state.step = 'login'

        st.markdown("---")
        st.write("**Fingerprint demo** — for judges: place any finger (or use camera) to simulate biometric unlock.")
        st.write("Use the *Place Finger* button for a fast demo, or use *Camera Scan* to show a live camera capture before unlocking.")

    with right:
        # fingerprint SVG (visual)
        fp_html = """
        <div style="display:flex;align-items:center;justify-content:center;">
          <svg width="140" height="140" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2C8.134 2 6 4.134 6 8v1" stroke="#6b7280" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M18 8c0-3.866-2.134-6-6-6S6 4.134 6 8v3c0 4.418-1 6 6 6s6-1.582 6-6V8z" stroke="#6b7280" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M12 14v4" stroke="#6b7280" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        """
        st.components.v1.html(fp_html, height=160)

        # Camera scan: capture finger image (optional show)
        camera_capture = st.camera_input("Camera Scan (optional) — capture finger image")
        # Place Finger button (simulates biometric scan)
        if st.button("Place Finger (Simulated Biometric)"):
            placeholder = st.empty()
            prog = placeholder.progress(0)
            # quick animated progress for realism
            for i in range(1, 101, 10):
                prog.progress(i)
                time.sleep(0.08)
            placeholder.success("Fingerprint accepted (demo)")
            # small pause so user sees success
            time.sleep(0.45)
            # set session flag and advance
            st.session_state.pin = 'biometric-demo'
            st.session_state.step = 'scan_barcode'

        # If user used camera capture, treat as scan and simulate fingerprint
        if camera_capture is not None:
            # show preview
            st.image(camera_capture.getvalue(), caption="Captured input (demo)", use_container_width=True)
            # automatically simulate scan (small progress)
            placeholder2 = st.empty()
            prog2 = placeholder2.progress(0)
            for i in range(1, 101, 20):
                prog2.progress(i)
                time.sleep(0.08)
            placeholder2.success("Camera fingerprint accepted (demo)")
            time.sleep(0.45)
            st.session_state.pin = 'biometric-demo'
            st.session_state.step = 'scan_barcode'



# ---------------------------
# Step: SCAN QR (camera-driven, auto-advance)
# ---------------------------
elif st.session_state.step == 'scan_qr':
    st.subheader('Step 2 — Scan Teacher QR (Session)')
    st.write('Point the camera at the teacher QR. Press Capture — any captured frame will be accepted and auto-advance.')

    cam_q = st.camera_input("Camera — point at teacher QR and Capture")
    if cam_q is not None:
        try:
            _ = cam_q.getvalue()
            # accept and set/keep session token
            token = st.session_state.get('current_session') or secrets.token_urlsafe(6)
            st.session_state.current_session = token
            st.session_state.step = 'face_match'
        except Exception:
            st.error("Capture failed — try again.")

    if st.button("Back"):
        st.session_state.step = 'scan_barcode'

# ---------------------------
# Step: FACE MATCH
# ---------------------------
elif st.session_state.step == 'face_match':
    st.subheader('Step 3 — Face detection / match (demo)')
    st.write('Take a selfie with camera or upload one. If a reference image exists (images/<college_id>.jpg) it will try a simple similarity check; otherwise demo accepts the selfie and grants attendance.')

    c1, c2 = st.columns(2)
    with c1:
        cam_img = st.camera_input("Take a selfie")
        uploaded = st.file_uploader("Or upload a selfie (png/jpg)", type=['png','jpg','jpeg'])
        chosen = None
        if cam_img is not None:
            chosen = cam_img
        elif uploaded is not None:
            chosen = uploaded

    with c2:
        st.write('Student record:')
        if st.session_state.user:
            st.write(f"**{st.session_state.user['name']}**")
            st.write(f"ID: {st.session_state.user['college_id']}")
        st.write(f"Barcode: {st.session_state.barcode}  |  Session: {st.session_state.get('current_session', '')}")

    # try load reference if present
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

    # demo reference optionally used if present
    demo_ref_bytes = None
    try:
        with open("images/_demo_student.jpg", "rb") as f:
            demo_ref_bytes = f.read()
    except Exception:
        demo_ref_bytes = None

    st.write("---")

    if chosen is not None:
        try:
            chosen_bytes = chosen.getvalue()
        except Exception:
            chosen_bytes = None

        if chosen_bytes is None:
            st.error("Could not read captured/uploaded image.")
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
                # demo: accept any captured selfie
                st.success("Demo: selfie captured — attendance granted.")
                st.session_state.attendance.insert(0, {
                    'name': st.session_state.user['name'],
                    'college_id': st.session_state.user['college_id'],
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'barcode': st.session_state.barcode,
                    'session': st.session_state.get('current_session')
                })
                st.session_state.step = 'done'

    if st.button("Back"):
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
