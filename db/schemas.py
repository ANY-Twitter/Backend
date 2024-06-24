from marshmallow import Schema, fields, validate, post_load
from datetime import datetime

class Usuario:
    def __init__(self, name, handle, password):
        self.name = name
        self.handle = handle
        self.password = password

class UsuarioSchema(Schema):
    name = fields.Str(load_default=None)
    handle = fields.Str(required=True)
    password = fields.Str(required=True)

    @post_load
    def make_usuario_object(self, data, **kwargs):
        return Usuario(**data)

class Tweet():
    def __init__(self, handle, data, date):
        self.handle = handle
        self.data = data
        self.date = date

class TweetSchema(Schema):
    handle = fields.Str(required=True)
    data = fields.Str(required=True)
    date = fields.DateTime(required=True)

    @post_load
    def make_tweet_object(self, data, **kwargs):
        return Tweet(**data)
    
class Message():
    def __init__(self, message, signedHash):
        self.message = message
        self.signedHash = signedHash

class MessageSchema(Schema):
    message = fields.Str(required=True)
    signedHash = fields.Str(required=True)

    @post_load
    def make_message_object(self, data, **kwargs):
        return Message(**data)