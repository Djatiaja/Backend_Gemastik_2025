from marshmallow import Schema, fields, validates, ValidationError, validate
from ..Models.User import User

class FavoriteSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    place_id = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    latitude = fields.Float(required=True, validate=validate.Range(min=-90, max=90))
    longitude = fields.Float(required=True, validate=validate.Range(min=-180, max=180))
    tags = fields.Dict(keys=fields.Str(), values=fields.Str(), allow_none=True)
    notes = fields.Str(allow_none=True)
    created_at = fields.DateTime(dump_only=True)

    @validates('user_id')
    def validate_user_id(self, Conan, value):
        if not User.query.get(value):
            raise ValidationError('User does not exist.')

    @validates('tags')
    def validate_tags(self, value):
        if value is None:
            return
        if not isinstance(value, dict):
            raise ValidationError('Tags must be a dictionary')