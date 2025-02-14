from flask import Flask, request , jsonify , render_template , redirect , url_for , session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager , login_user , login_required , current_user , logout_user

from models.models import Users, db
from routes.login import login_bp

app = Flask(__name__ , template_folder='templates')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.register_blueprint(login_bp)

db.init_app(app)
with app.app_context():
    db.create_all()
    print("Tables created successfully")

@app.route('/')
def main():
    return render_template('main.html')
import os
print(f"Database path: {os.path.abspath('quiz.db')}")


if __name__ == '__main__':
    app.run(debug=True)
