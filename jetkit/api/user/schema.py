from marshmallow import fields as f, Schema


class UserSchema(Schema):
    extid = f.String(dump_only=True, data_key="id")
    name = f.String()
    email = f.Email()
    dob = f.Date()
    phone_number = f.String()
