from flask import Blueprint, request, jsonify, session, redirect, url_for
from marshmallow import ValidationError
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from .authSchema import UserSchema, LoginSchema
from ..Models.User import User, db
from flask_dance.contrib.google import google
from ...Utils.Response import base_response

auth_bp = Blueprint('auth', __name__)

user_schema = UserSchema()
login_schema = LoginSchema()

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = user_schema.load(request.get_json())
        
        # Create new user
        user = User(
            email=data['email'],
            name=data.get('name'),
            password_hash=generate_password_hash(data['password']) if data.get('password') else None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify(base_response(
            code=201,
            status='success',
            message='User registered successfully',
            data=user_schema.dump(user)
        )), 201
    except ValidationError as err:
        return jsonify(base_response(
            code=400,
            status='error',
            message='Validation error',
            error=err.messages
        )), 400
    except Exception as e:
        return jsonify(base_response(
            code=500,
            status='error',
            message='Internal server error',
            error=str(e)
        )), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = login_schema.load(request.get_json())
        
        user = User.query.filter_by(email=data['email']).first()
        
        if not user or (user.password_hash and not check_password_hash(user.password_hash, data['password'])):
            return jsonify(base_response(
                code=401,
                status='error',
                message='Invalid credentials'
            )), 401
            
        session['user_id'] = user.user_id
        return jsonify(base_response(
            code=200,
            status='success',
            message='Login successful',
            data=user_schema.dump(user)
        )), 200
    except ValidationError as err:
        return jsonify(base_response(
            code=400,
            status='error',
            message='Validation error',
            error=err.messages
        )), 400
    except Exception as e:
        return jsonify(base_response(
            code=500,
            status='error',
            message='Internal server error',
            error=str(e)
        )), 500

@auth_bp.route('/google_login')
def google_login():
    if not google.authorized:
        return redirect(url_for("google.login"))
    
    try:
        resp = google.get("/oauth2/v2/userinfo")
        if not resp.ok:
            return jsonify(base_response(
                code=400,
                status='error',
                message='Failed to fetch user info'
            )), 400
            
        google_info = resp.json()
        google_id = google_info['id']
        email = google_info['email']
        
        user = User.query.filter_by(google_id=google_id).first()
        
        if not user:
            user = User(
                email=email,
                name=google_info.get('name'),
                google_id=google_id,
                profile_picture_url=google_info.get('picture'),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(user)
            db.session.commit()
        
        session['user_id'] = user.user_id
        return jsonify(base_response(
            code=200,
            status='success',
            message='Google login successful',
            data=user_schema.dump(user)
        )), 200
    except Exception as e:
        return jsonify(base_response(
            code=500,
            status='error',
            message='Internal server error',
            error=str(e)
        )), 500

@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    return jsonify(base_response(
        code=200,
        status='success',
        message='Logged out successfully'
    )), 200