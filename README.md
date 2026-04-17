# Real Time Face Recognition

This guide provides step-by-step instructions for setting up the environment, installing necessary dependencies (including required C++ compilers for face recognition), and running the application.

## Prerequisites & Python Setup

### Step 1: Download and Install Python 3.11
1. Go to the official Python download page for Windows: [Python 3.11 Releases](https://www.python.org/downloads/windows/).
2. Scroll down and download the Windows installer (64-bit) for the latest 3.11 version (e.g., Python 3.11.9).
3. Run the installer.
4. **Important:** At the bottom of the installer window, you can leave *"Add python.exe to PATH"* unchecked if you want to keep newer versions (like 3.13) as your main system Python. The Windows `py` launcher will still automatically find 3.11. 
5. Click **Install Now**.

### Step 2: Create a 3.11 Virtual Environment
Once installed, open your PowerShell terminal in your project folder (`C:\Face_ID_recognition`) and tell the Python Launcher (`py`) to specifically use version 3.11 to create an isolated environment for this project:

```powershell
py -3.11 -m venv venv
```

### Step 3: Activate the Environment
Turn on the newly created virtual environment:

```powershell
.\venv\Scripts\activate
```

### Step 4: Install the C++ Build Tools
1. Go to the official Microsoft download page: Visual Studio Build Tools.
2. Download and run the Build Tools installer.
3. When the installer opens, you will see a grid of options. Check the box for "Desktop development with C++".
4. Look at the "Installation details" panel on the right side. Ensure that the MSVC v143 - VS 2022 C++ x64/x86 build tools and the Windows 11 SDK (or Windows 10 SDK) are checked.
5. Click Install. (Note: This is a large download, usually around 6-8 GB).

### Step 5: Refresh Your Environment
1. The newly installed compilers will not be recognized by your current terminal session.
2. Close your PowerShell/VS Code completely.
3. Reopen your terminal.
4. Navigate back to your project and activate the Python 3.11 environment again:

```powershell
cd C:\Face_ID_recognition
.\venv\Scripts\activate
```

### Step 6: Install Requirements
With your virtual environment activated and C++ tools installed, install the project dependencies:

```powershell
pip install -r requirements.txt
```

### Step 7: Run the Backend (FastAPI)
Start the FastAPI server:

```powershell
py -m uvicorn main:app --reload
```

### Step 8: Run the Frontend (Streamlit)
Open a new terminal, activate the virtual environment again, and start the Streamlit interface

```powershell
py -m streamlit run app.py
```
