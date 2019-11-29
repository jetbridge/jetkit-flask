from marshmallow import fields as f, Schema


class UserSchema(Schema):
    id = f.Integer()
    name = f.String()
    email = f.String()
    dob = f.Date()
    phone_number = f.String()
