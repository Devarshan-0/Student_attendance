
Streamlit Student Attendance Prototype
-------------------------------------

What this package contains:
- streamlit_app.py : single-file Streamlit prototype (simulated flow)
- requirements.txt : dependencies

How to run locally:
1. Install Python 3.8+ and pip if not present.
2. Create a virtual environment (recommended):
   python -m venv venv
   source venv/bin/activate   # macOS / Linux
   venv\Scripts\activate    # Windows PowerShell
3. Install requirements:
   pip install -r requirements.txt
4. Run the app:
   streamlit run streamlit_app.py
5. Open the URL shown in the terminal (usually http://localhost:8501).

How to upload to GitHub & deploy on Streamlit Cloud:
1. Create a new GitHub repository (public or private).
2. Commit the files from this folder and push to the repo.
   Example commands:
     git init
     git add .
     git commit -m "Add Streamlit attendance prototype"
     git branch -M main
     git remote add origin https://github.com/<your-username>/<repo-name>.git
     git push -u origin main
3. Go to https://share.streamlit.io/ and click 'Sign in with GitHub'.
4. Click 'New app', select the repository and branch `main`, and set the main file path to `streamlit_app.py`.
5. Click 'Deploy'. Streamlit Cloud will build and run the app for you.
Notes:
- The app currently simulates barcode/QR scanning and face matching. Replace simulated sections with real libraries (camera access, face recognition models, barcode/QR libraries) for production.
