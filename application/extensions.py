from flask_cors import CORS
from flask_bcrypt import Bcrypt

cors = CORS()
bcrypt = Bcrypt()

all = [cors, bcrypt]