from .db_session import SqlAlchemyBase
import sqlalchemy
import time
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin
from datetime import datetime


class User(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'users'
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
    articles = sqlalchemy.orm.relationship("Article", back_populates="author")


    def to_json(self):
        exam_json = self.to_dict(only=('id', 'name', 'surname', 'age', 'nickname', 'gender'))
        return exam_json


class Article(SqlAlchemyBase):
    __tablename__ = 'articles'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    author_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    author = orm.relationship("User")
    title = sqlalchemy.Column(sqlalchemy.String(64), unique=True, nullable=False)
    date = sqlalchemy.Column(sqlalchemy.Integer, nullable=False, default=int(time.time()))
    content = sqlalchemy.Column(sqlalchemy.Text, nullable=False)
    template = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    image = sqlalchemy.Column(sqlalchemy.String(100), nullable=False)
