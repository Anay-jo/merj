# Flask Backend Setup Instructions

## Step 1: Create Virtual Environment
```bash
cd flask_backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

## Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

## Step 3: Run the Flask Server
```bash
python app.py
```

The server will start on http://127.0.0.1:5000

## Project Structure
```
flask_backend/
├── app.py              # Main Flask application
├── requirements.txt     # Python dependencies
├── venv/               # Virtual environment (created after setup)
└── README.md           # This file
```

## Dependencies
- Flask 2.3.3: Web framework
- Flask-CORS 4.0.0: Cross-Origin Resource Sharing support
