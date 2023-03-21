from .db_session import SqlAlchemyBase
import sqlalchemy
import time
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin
from datetime import datetime, timezone


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
    likes = sqlalchemy.orm.relationship("Like", back_populates="liker")

    def to_json(self):
        user_json = self.to_dict(only=('id', 'name', 'surname', 'age', 'nickname', 'gender'))
        return user_json


class Article(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'articles'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    author_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    author = orm.relationship("User")
    title = sqlalchemy.Column(sqlalchemy.String(64), unique=True, nullable=False)
    date = sqlalchemy.Column(sqlalchemy.Integer, nullable=False, default=int(time.time()))
    content = sqlalchemy.Column(sqlalchemy.Text, nullable=False)
    template = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    image = sqlalchemy.Column(sqlalchemy.String(100), nullable=False)
    likes = sqlalchemy.orm.relationship("Like", back_populates="liked")

    def to_json(self):
        article = self.to_dict(only=('id', 'title', 'content', 'image', 'template'))
        article['author'] = self.author.to_json()
        article['date'] = datetime.fromtimestamp(self.date, timezone.utc).astimezone().isoformat()
        return article


class Like(SqlAlchemyBase):
    __tablename__ = 'likes'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    liker_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    liker = orm.relationship("User")
    liked_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('articles.id'))
    liked = orm.relationship("Article")
