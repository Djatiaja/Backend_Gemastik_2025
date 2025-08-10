from flask import Blueprint, request, session
from werkzeug.exceptions import BadRequest, Unauthorized
from ...Utils.Response import base_response
from .placeSchema import PlaceSchema
import overpy
import requests
from marshmallow import Schema, fields, validate

places_bp = Blueprint('places', __name__, url_prefix='/places')

# Authentication check
def require_auth():
    if 'user_id' not in session:
        return
        raise Unauthorized(description='Authentication required')

# Define schema for directions response
class RouteSchema(Schema):
    distance = fields.Float(required=True)
    time = fields.Integer(required=True)
    instructions = fields.List(
        fields.Dict(
            keys=fields.Str(),
            values=fields.Raw(),
        ),
    )
    coordinates = fields.List(
        fields.List(
            fields.Float(),
            validate=validate.Length(min=2, max=2),
        ),
    )

# Existing /nearby endpoint
@places_bp.route('/nearby', methods=['GET'])
def get_nearby_places():
    try:
        require_auth()
        lat = float(request.args.get('lat', 0))
        lon = float(request.args.get('lon', 0))
        radius = int(request.args.get('radius', 10000))
        place_type = 'cafe'
        name = request.args.get('name', '')

        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            raise BadRequest(description='Invalid latitude or longitude')
        if radius < 100 or radius > 10000:
            raise BadRequest(description='Radius must be between 100 and 10000 meters')
        if place_type.strip() == '':
            raise BadRequest(description='Place type cannot be empty')

        api = overpy.Overpass()
        name_filter = f'["name"~"{name}",i]' if name.strip() else ''
        query = f"""
            [out:json];
            node["amenity"="{place_type}"]{name_filter}(around:{radius},{lat},{lon});
            out body;
        """

        result = api.query(query)
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

# Existing /directions endpoint
@places_bp.route('/directions', methods=['GET'])
def get_walking_directions():
    try:
        require_auth()
        start_lat = float(request.args.get('start_lat'))
        start_lon = float(request.args.get('start_lon'))
        end_lat = float(request.args.get('end_lat'))
        end_lon = float(request.args.get('end_lon'))

        if not (-90 <= start_lat <= 90) or not (-180 <= start_lon <= 180):
            raise BadRequest(description='Invalid start latitude or longitude')
        if not (-90 <= end_lat <= 90) or not (-180 <= end_lon <= 180):
            raise BadRequest(description='Invalid end latitude or longitude')

        OSRM_URL = 'http://router.project-osrm.org/route/v1/foot'
        coordinates = f'{start_lon},{start_lat};{end_lon},{end_lat}'
        params = {
            'overview': 'full',
            'geometries': 'geojson',
            'steps': 'true'
        }

        response = requests.get(f'{OSRM_URL}/{coordinates}', params=params)
        response.raise_for_status()
        data = response.json()

        if data.get('code') != 'Ok' or not data.get('routes'):
            raise BadRequest(description='No route found')

        route_data = data['routes'][0]
        instructions = []
        for leg in route_data['legs']:
            for step in leg['steps']:
                maneuver = step.get('maneuver', {})
                instruction = maneuver.get('instruction', '')
                if not instruction:
                    maneuver_type = maneuver.get('type', 'unknown')
                    if maneuver_type == 'depart':
                        instruction = f"Mulai berjalan dari titik awal di {step.get('name', 'jalan tanpa nama')}"
                    elif maneuver_type == 'arrive':
                        instruction = f"Sampai di tujuan di {step.get('name', 'jalan tanpa nama')}"
                    else:
                        instruction = f"Lanjutkan berjalan di {step.get('name', 'jalan tanpa nama')} sejauh {step['distance']} meter"

                if step.get('name'):
                    instruction = f"Di {step['name']}: {instruction}"
                if step.get('access') == 'tactile_paving':
                    instruction += " (ada jalur taktil untuk tunanetra)"

                instructions.append({
                    'text': instruction,
                    'distance': step['distance'],
                    'interval': maneuver.get('location', [])
                })

        route = {
            'distance': route_data['distance'],
            'time': int(route_data['duration']),
            'instructions': instructions,
            'coordinates': route_data['geometry']['coordinates']
        }

        schema = RouteSchema()
        result = schema.dump(route)

        return base_response(
            code=200,
            status='success',
            message='Rute berjalan berhasil diambil',
            data={'route': result}
        )

    except ValueError:
        return base_response(
            code=400,
            status='error',
            message='Parameter masukan tidak valid',
            error={'parameters': 'Format tidak valid'}
        )
    except requests.exceptions.HTTPError as e:
        return base_response(
            code=500,
            status='error',
            message='Kesalahan layanan OSRM',
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

# New /search endpoint
@places_bp.route('/search', methods=['GET'])
def search_places():
    try:
        require_auth()
        # Get query parameters
        query = request.args.get('query', '').strip()
        lat = float(request.args.get('lat', 0))
        lon = float(request.args.get('lon', 0))
        radius = int(request.args.get('radius', 10000))
        tags = request.args.get('tags', '').strip().split(',') if request.args.get('tags') else []

        # Validate inputs
        if not query and not tags:
            raise BadRequest(description='Query or tags must be provided')
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            raise BadRequest(description='Invalid latitude or longitude')
        if radius < 100 or radius > 10000:
            raise BadRequest(description='Radius must be between 100 and 10000 meters')

        # Initialize Overpass API
        api = overpy.Overpass()

        # Construct Overpass query
        tag_filters = ''.join([f'["{tag.strip()}"]' for tag in tags if tag.strip()]) if tags else ''
        name_filter = f'["name"~"{query}",i]' if query else ''
        query_str = f"""
            [out:json];
            node{tag_filters}{name_filter}(around:{radius},{lat},{lon});
            out body;
        """

        # Execute query
        result = api.query(query_str)

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