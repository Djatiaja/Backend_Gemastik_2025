from marshmallow import Schema, fields, ValidationError, validates

class PlaceSchema(Schema):
    id = fields.Str(required=True)
    name = fields.Str(required=True)
    latitude = fields.Float(required=True)
    longitude = fields.Float(required=True)
    tags = fields.Dict(keys=fields.Str(), values=fields.Str(), allow_none=True)

    @validates('tags')
    def validate_tags(self, value):
        if value is None:
            return
        if not isinstance(value, dict):
            raise ValidationError('Tags must be a dictionary')