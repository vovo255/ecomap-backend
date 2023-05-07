from .db_session import SqlAlchemyBase
import sqlalchemy
import time
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin
from datetime import datetime, timezone
from json import loads


class User(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'users'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    surname = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    age = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    nickname = sqlalchemy.Column(sqlalchemy.String, nullable=False, unique=True)
    gender = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    email = sqlalchemy.Column(sqlalchemy.String, unique=True, nullable=False)
    rate = sqlalchemy.Column(sqlalchemy.Integer, nullable=False, default=10)
    is_admin = sqlalchemy.Column(sqlalchemy.Boolean, nullable=False, default=False)
    password_hash = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    salt = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    create_date = sqlalchemy.Column(sqlalchemy.Integer, nullable=False, default=int(time.time()))
    token = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    expires_at = sqlalchemy.Column(sqlalchemy.Integer)
    articles = sqlalchemy.orm.relationship("Article", back_populates="author")
    points = sqlalchemy.orm.relationship("Point", back_populates="user")
    likes = sqlalchemy.orm.relationship("Like", back_populates="liker")
    favorites = sqlalchemy.orm.relationship("Favorite", back_populates="fav_user")
    subscribers = sqlalchemy.orm.relationship("Subscribe", back_populates="subscribed_to_user")
    subscribed_to = sqlalchemy.orm.relationship("Subscribe", back_populates="subscriber_user")
    avatar = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    def to_json(self):
        user_json = self.to_dict(
            only=('id', 'name', 'surname', 'age', 'nickname', 'gender', 'rate', 'is_admin', 'email', 'avatar'))
        user_json['points'] = []
        for point in self.points:
            point: Point
            user_json['points'].append(point.to_json())
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
        user_liked = []
        for like in self.likes:
            user_liked.append(like.liker_id)
        article['user_liked'] = user_liked
        return article

    def get_short_desc(self):
        article = self.to_dict(only=('id', 'image', 'title'))
        article['countOfLikes'] = len(self.likes)
        users_liked = {}
        for like in self.likes:
            users_liked[like.liker_id] = [like.liker.name, like.liker.surname, like.liker.avatar]
        article['user_liked'] = users_liked
        return article


class Like(SqlAlchemyBase):
    __tablename__ = 'likes'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    liker_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    liker = orm.relationship("User")
    liked_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('articles.id'))
    liked = orm.relationship("Article")


class Favorite(SqlAlchemyBase):
    __tablename__ = 'Favorites'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    fav_user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    fav_user = orm.relationship("User")
    fav_point_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('points.id'))
    fav_point = orm.relationship("Point")


class Subscribe(SqlAlchemyBase):
    __tablename__ = 'Subscribes'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    subscribed_to_user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    subscribed_to_user = orm.relationship("User")
    subscriber_user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    subscriber_user = orm.relationship("User")


class Point(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'points'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=False, default="")
    icon = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    address = sqlalchemy.Column(sqlalchemy.String, nullable=False, default="")
    pointX = sqlalchemy.Column(sqlalchemy.Float, nullable=False)
    pointY = sqlalchemy.Column(sqlalchemy.Float, nullable=False)
    types = sqlalchemy.Column(sqlalchemy.String, nullable=False, default='[]')
    images = sqlalchemy.Column(sqlalchemy.String, nullable=False, default='[]')
    comment = sqlalchemy.Column(sqlalchemy.String, nullable=False, default='')
    is_accepted = sqlalchemy.Column(sqlalchemy.Boolean, nullable=False, default=False)
    user = orm.relationship("User")
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    favorites = sqlalchemy.orm.relationship("Favorite", back_populates="fav_point")

    def to_json(self):
        point = self.to_dict(only=('title', 'icon', 'address', 'pointX', 'pointY', 'comment', 'types', 'id'))
        point['iconImageHref'] = self.icon
        point['images'] = loads(self.images)
        return point
    

class Notification(SqlAlchemyBase):
    __tablename__ = 'notifications'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True ,autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    date = sqlalchemy.Column(sqlalchemy.Integer, nullable=False, default=int(time.time()))
    notification_type = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    user = orm.relationship('User')
    point = orm.relationship('Point')


    
