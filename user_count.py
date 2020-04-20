from app import app
from ahmaths.models import User

with app.app_context():
    print(len(User.query.all()))
