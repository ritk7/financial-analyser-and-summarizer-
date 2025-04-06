from flask import Flask
from flask_login import LoginManager
import os
from config import Config

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Import and initialize database
from models import init_db
init_db()

# Import and initialize routes after defining app and login_manager
from routes import init_routes
init_routes(app)

if __name__ == '__main__':
    # Create uploads directory if it doesn't exist
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    
    # Run the app
    app.run(debug=True)