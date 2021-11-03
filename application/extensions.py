from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager

cors = CORS()
bcrypt = Bcrypt()
jwt = JWTManager()

all = [cors, bcrypt, jwt]