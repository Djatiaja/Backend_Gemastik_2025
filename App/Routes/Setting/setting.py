from flask import Blueprint, request, session
from flask_sqlalchemy import SQLAlchemy
from marshmallow import ValidationError
from ..Models.Setting import Settings
from .settingSchema import SettingsSchema, SettingsUpdateSchema
from ...Utils.Response import base_response
from werkzeug.exceptions import NotFound, Unauthorized

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')
db = SQLAlchemy()

# Middleware to check if user is authenticated
def require_auth():
    if 'user_id' not in session:
        raise Unauthorized(description='Authentication required')

@settings_bp.route('', methods=['GET'])
def get_settings():
    try:
        require_auth()
        user_id = session['user_id']
        settings = Settings.query.filter_by(user_id=user_id).first()
        if not settings:
            raise NotFound(description='Settings not found')
        schema = SettingsSchema()
        return base_response(
            code=200,
            status='success',
            message='Settings retrieved successfully',
            data=schema.dump(settings)
        )
    except NotFound as e:
        return base_response(
            code=404,
            status='error',
            message=str(e),
            error={'settings': 'Not found'}
        )
    except Exception as e:
        return base_response(
            code=500,
            status='error',
            message='Internal server error',
            error=str(e)
        )

@settings_bp.route('', methods=['PUT'])
def update_settings():
    try:
        require_auth()
        user_id = session['user_id']
        data = request.get_json()
        settings = Settings.query.filter_by(user_id=user_id).first()
        if not settings:
            raise NotFound(description='Settings not found')

        schema = SettingsUpdateSchema()
        settings_data = schema.load(data, partial=True)
        for key, value in settings_data.items():
            setattr(settings, key, value)
        db.session.commit()
        return base_response(
            code=200,
            status='success',
            message='Settings updated successfully',
            data=schema.dump(settings)
        )
    except ValidationError as e:
        return base_response(
            code=400,
            status='error',
            message='Validation error',
            error=e.messages
        )
    except NotFound as e:
        return base_response(
            code=404,
            status='error',
            message=str(e),
            error={'settings': 'Not found'}
        )
    except Exception as e:
        db.session.rollback()
        return base_response(
            code=500,
            status='error',
            message='Internal server error',
            error=str(e)
        )