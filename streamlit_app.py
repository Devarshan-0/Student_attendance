
import streamlit as st
from datetime import datetime

# Simple Student Attendance prototype in Streamlit (simulated)
# Steps: Login -> App Lock PIN -> Scan Barcode -> Scan QR -> Face Match (simulated)
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
            st.experimental_rerun()
    if col2.button('Reset'):
        reset_all()
        st.experimental_rerun()

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
            st.experimental_rerun()
    if col2.button('Back to Login'):
        st.session_state.step = 'login'
        st.experimental_rerun()

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
            st.experimental_rerun()
    if col2.button('Back'):
        st.session_state.step = 'applock'
        st.experimental_rerun()

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
            st.experimental_rerun()
    if col2.button('Back'):
        st.session_state.step = 'scan_barcode'
        st.experimental_rerun()

elif st.session_state.step == 'face_match':
    st.subheader('Step 3 — Face detection / match')
    st.write('Simulated: upload a photo or click the simulate-match button. In production, replace with face recognition model.')
    col1, col2 = st.columns(2)
    with col1:
        uploaded = st.file_uploader('Upload a selfie (optional, simulated)', type=['png','jpg','jpeg'])
        st.write('Camera preview placeholder below (streamlit cannot access camera in all hosts).')
        st.empty()
    with col2:
        st.write('Student record (reference)')
        if st.session_state.user:
            st.write(f"**{st.session_state.user['name']}**\n\nID: {st.session_state.user['college_id']}")
        st.write(f"Barcode: {st.session_state.barcode}\n\nQR: {st.session_state.qr}")
    st.write('---')
    col1, col2 = st.columns(2)
    if col1.button('Simulate Successful Match'):
        entry = {
            'name': st.session_state.user['name'],
            'college_id': st.session_state.user['college_id'],
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'barcode': st.session_state.barcode,
            'qr': st.session_state.qr,
        }
        st.session_state.attendance.insert(0, entry)
        st.session_state.step = 'done'
        st.experimental_rerun()
    if col2.button('Simulate Failed Match'):
        st.error('Face did not match — attendance denied')
    if st.button('Back'):
        st.session_state.step = 'scan_qr'
        st.experimental_rerun()

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
        st.experimental_rerun()
    if col2.button('Logout'):
        reset_all()
        st.experimental_rerun()

st.sidebar.title('Attendance Log')
if st.session_state.attendance:
    for a in st.session_state.attendance:
        st.sidebar.write(f"**{a['name']}** — {a['college_id']}")
        st.sidebar.write(a['time'])
        st.sidebar.markdown('---')
else:
    st.sidebar.write('No entries yet.')
