from marshmallow import Schema, fields, validates, ValidationError, validate

class SettingsSchema(Schema):
    settings_id = fields.Int(dump_only=True)
    user_id = fields.Int(required=True)
    volume = fields.Float(required=True, validate=validate.Range(min=0.0, max=1.0))
    gender_voice = fields.Str(required=True, validate=validate.OneOf(['male', 'female']))
    provider_voice = fields.Str(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    @validates('user_id')
    def validate_user_id(self, value):
        from Models.User import User
        if not User.query.get(value):
            raise ValidationError('User does not exist.')

class SettingsUpdateSchema(SettingsSchema):
    volume = fields.Float(required=False, validate=validate.Range(min=0.0, max=1.0))
    gender_voice = fields.Str(required=False, validate=validate.OneOf(['male', 'female']))
    user_id = fields.Int(dump_only=True)  # Prevent updating user_id