from marshmallow import Schema, fields, validates, ValidationError
from ..Models.User import User

class UserSchema(Schema):
    user_id = fields.Int(dump_only=True)
    email = fields.Email(required=True)
    name = fields.Str(required=False, allow_none=True)
    password = fields.Str(required=False, load_only=True, allow_none=True)
    google_id = fields.Str(required=False, allow_none=True)
    profile_picture_url = fields.Str(required=False, allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    @validates('email')
    def validate_email(self, value):
        if User.query.filter_by(email=value).first():
            raise ValidationError('Email already exists')

    @validates('google_id')
    def validate_google_id(self, value):
        if value and User.query.filter_by(google_id=value).first():
            raise ValidationError('Google ID already exists')

class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)