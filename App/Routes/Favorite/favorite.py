from flask import Blueprint, request, session
from flask_sqlalchemy import SQLAlchemy
from marshmallow import ValidationError
from ..Models.Favorite import Favorite
from .favoriteShema import FavoriteSchema
from ...Utils.Response import base_response
from werkzeug.exceptions import NotFound, Unauthorized, BadRequest

favorites_bp = Blueprint('favorites', __name__, url_prefix='/favorites')
db = SQLAlchemy()

def require_auth():
    if 'user_id' not in session:
        return
        raise Unauthorized(description='Authentication required')

@favorites_bp.route('', methods=['POST'])
def add_favorite():
    try:
        require_auth()
        user_id = session['user_id']
        data = request.get_json()
        data['user_id'] = user_id  # Enforce user_id from session
        schema = FavoriteSchema()
        favorite_data = schema.load(data)

        # Check if favorite already exists
        existing = Favorite.query.filter_by(user_id=user_id, place_id=favorite_data['place_id']).first()
        if existing:
            raise BadRequest(description='Place already in favorites')

        # Create new favorite
        favorite = Favorite(
            user_id=favorite_data['user_id'],
            place_id=favorite_data['place_id'],
            name=favorite_data['name'],
            latitude=favorite_data['latitude'],
            longitude=favorite_data['longitude'],
            tags=str(favorite_data.get('tags', {})),
            notes=favorite_data.get('notes')
        )
        db.session.add(favorite)
        db.session.commit()

        return base_response(
            code=201,
            status='success',
            message='Favorite added successfully',
            data=schema.dump(favorite)
        )

    except ValidationError as e:
        return base_response(
            code=400,
            status='error',
            message='Validation error',
            error=e.messages
        )
    except BadRequest as e:
        return base_response(
            code=400,
            status='error',
            message=str(e),
            error={'favorite': str(e)}
        )
    except Exception as e:
        db.session.rollback()
        return base_response(
            code=500,
            status='error',
            message='Internal server error',
            error=str(e)
        )

@favorites_bp.route('', methods=['GET'])
def get_favorites():
    try:
        require_auth()
        user_id = session['user_id']
        favorites = Favorite.query.filter_by(user_id=user_id).all()
        schema = FavoriteSchema(many=True)
        return base_response(
            code=200,
            status='success',
            message='Favorites retrieved successfully',
            data={'favorites': schema.dump(favorites), 'count': len(favorites)}
        )

    except Exception as e:
        return base_response(
            code=500,
            status='error',
            message='Internal server error',
            error=str(e)
        )

@favorites_bp.route('/<place_id>', methods=['DELETE'])
def remove_favorite(place_id):
    try:
        require_auth()
        user_id = session['user_id']
        favorite = Favorite.query.filter_by(user_id=user_id, place_id=place_id).first()
        if not favorite:
            raise NotFound(description='Favorite not found')

        db.session.delete(favorite)
        db.session.commit()
        return base_response(
            code=200,
            status='success',
            message='Favorite removed successfully'
        )

    except NotFound as e:
        return base_response(
            code=404,
            status='error',
            message=str(e),
            error={'favorite': 'Not found'}
        )
    except Exception as e:
        db.session.rollback()
        return base_response(
            code=500,
            status='error',
            message='Internal server error',
            error=str(e)
        )