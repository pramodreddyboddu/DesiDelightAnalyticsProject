# This file makes the src directory a Python package

from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    # ... existing config ...
    CORS(app, supports_credentials=True, origins=[
        'https://desi-delight-analytics-project.vercel.app'
    ], allow_headers=['Content-Type', 'X-API-KEY'])
    # ... rest of app setup ...
    return app
