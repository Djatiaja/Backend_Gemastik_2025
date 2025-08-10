import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from App.Routes.Auth.auth import auth_bp
from flask_dance.contrib.google import make_google_blueprint
from App.Routes.Setting.setting import settings_bp
from App.Routes.Favorite.favorite import favorites_bp
from App.Routes.Places.place import places_bp
from App.Routes.Auth.auth import auth_bp
from App.Routes.CV.cv import inference_bp

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config["GOOGLE_OAUTH_CLIENT_ID"] = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
app.config["GOOGLE_OAUTH_CLIENT_SECRET"] = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")

db = SQLAlchemy(app)
google_bp = make_google_blueprint(scope=["profile", "email"])

app.register_blueprint(settings_bp)
app.register_blueprint(places_bp)
app.register_blueprint(favorites_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(inference_bp)
app.register_blueprint(google_bp, url_prefix="/login")

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)