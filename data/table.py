from .db_session import SqlAlchemyBase
import sqlalchemy
import time


class User(SqlAlchemyBase):
    __tablename__ = 'player_island'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    surname = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    age = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    nickname = sqlalchemy.Column(sqlalchemy.String, nullable=False, unique=True)
    gender = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    email = sqlalchemy.Column(sqlalchemy.String, unique=True, nullable=False)
    password_hash = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    salt = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    create_date = sqlalchemy.Column(sqlalchemy.Integer, nullable=False, default=int(time.time()))
    token = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    expires_at = sqlalchemy.Column(sqlalchemy.Integer)
