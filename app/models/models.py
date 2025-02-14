from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship , backref
db = SQLAlchemy()

class Users(db.Model):
    __tablename__ = 'Users'
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(50), unique = True , nullable = False)
    password_hash = db.Column(db.String(50), nullable = False)
    role = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(50), unique = True, nullable = False)


  
