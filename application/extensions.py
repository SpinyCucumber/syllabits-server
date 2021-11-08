from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from bson.objectid import ObjectId

from .models import User

cors = CORS()
bcrypt = Bcrypt()
jwt = JWTManager()

# Set up automatic user serialization/deserialization
@jwt.user_identity_loader
def user_identity_lookup(user):
    return str(user.id)

@jwt.user_lookup_loader
def user_lookup_callback(jwt_header, jwt_data):
    identity = ObjectId(jwt_data["sub"])
    return User.objects(pk=identity).get()

@jwt.additional_claims_loader
def additional_claims_callback(user):
    return { 'is_admin': user.is_admin }

all = [cors, bcrypt, jwt]