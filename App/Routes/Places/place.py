from flask import Blueprint, request, session
from werkzeug.exceptions import BadRequest, Unauthorized
from ...Utils.Response import base_response
from .placeSchema import PlaceSchema
import overpy

places_bp = Blueprint('places', __name__, url_prefix='/places')

def require_auth():
    if 'user_id' not in session:
        raise Unauthorized(description='Authentication required')

@places_bp.route('/nearby', methods=['GET'])
def get_nearby_places():
    try:
        require_auth()
        # Get query parameters
        lat = float(request.args.get('lat', 0))
        lon = float(request.args.get('lon', 0))
        radius = int(request.args.get('radius', 1000))  # Default 1000 meters
        place_type = request.args.get('type', 'cafe')  # Default to cafe
        name = request.args.get('name', '')  # Optional name filter

        # Validate inputs
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            raise BadRequest(description='Invalid latitude or longitude')
        if radius < 100 or radius > 10000:
            raise BadRequest(description='Radius must be between 100 and 10000 meters')
        if place_type.strip() == '':
            raise BadRequest(description='Place type cannot be empty')

        # Initialize Overpass API
        api = overpy.Overpass()

        # Construct Overpass query
        name_filter = f'["name"~"{name}",i]' if name.strip() else ''
        query = f"""
            [out:json];
            node["amenity"="{place_type}"]{name_filter}(around:{radius},{lat},{lon});
            out body;
        """

        # Execute query
        result = api.query(query)

        # Process results
        places = [
            {
                'id': str(node.id),
                'name': node.tags.get('name', 'Unknown'),
                'latitude': float(node.lat),
                'longitude': float(node.lon),
                'tags': node.tags
            }
            for node in result.nodes
        ]

        # Serialize with Marshmallow
        schema = PlaceSchema(many=True)
        result = schema.dump(places)
        return base_response(
            code=200,
            status='success',
            message='Places retrieved successfully',
            data={'places': result, 'count': len(result)}
        )

    except ValueError:
        return base_response(
            code=400,
            status='error',
            message='Invalid input parameters',
            error={'parameters': 'Invalid format'}
        )
    except overpy.exception.OverPyException as e:
        return base_response(
            code=500,
            status='error',
            message='Overpass API error',
            error=str(e)
        )
    except BadRequest as e:
        return base_response(
            code=400,
            status='error',
            message=str(e),
            error={'parameters': str(e)}
        )
    except Exception as e:
        return base_response(
            code=500,
            status='error',
            message='Internal server error',
            error=str(e)
        )