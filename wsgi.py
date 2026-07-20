import sys
import os
import traceback

# Get the directory where this wsgi.py file is located
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# Add the project directory to the Python path
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

# Add the assets directory to the Python path
ASSETS_DIR = os.path.join(PROJECT_DIR, 'assets')
if ASSETS_DIR not in sys.path:
    sys.path.insert(0, ASSETS_DIR)

try:
    # Import the Flask app
    from app import app as application
    
    # Verify the app was imported correctly
    if application is None:
        raise RuntimeError("Flask app import returned None")
        
except Exception as e:
    # Create a simple error app if import fails
    from flask import Flask
    application = Flask(__name__)
    
    @application.route('/')
    def error_page():
        return f"""
        <h1>Import Error</h1>
        <p>Error: {str(e)}</p>
        <pre>{traceback.format_exc()}</pre>
        <h2>Debug Info</h2>
        <p>PROJECT_DIR: {PROJECT_DIR}</p>
        <p>ASSETS_DIR: {ASSETS_DIR}</p>
        <p>sys.path: {sys.path}</p>
        """, 500

# PythonAnywhere requires the WSGI callable to be named 'application'
