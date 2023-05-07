import json
import time
from flask import send_from_directory, Response
import flask
from flask import Flask, jsonify, request, make_response
from data import db_session
from datetime import datetime, timedelta, timezone
from data.table import User, Article, Like, Point, Favorite, Subscribe, Notification
from user_help import check_password, make_password, generate_token
from settings import DB_CONN_STR, TOKEN_LIVE_TIME_S, UPLOAD_FOLDER, ALLOWED_EXTENSIONS, DOMEN
import traceback
from werkzeug.utils import secure_filename
from json import dumps
import os
from flask_cors import CORS

blueprint = flask.Blueprint('main_api', __name__,
                            template_folder='api_templates')


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@blueprint.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        res = Response()
        res.headers['X-Content-Type-Options'] = '*'
        res.headers['Access-Control-Allow-Origin'] = '*'
        res.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE'
        res.headers['Access-Control-Allow-Headers'] = '*'
        return res


@blueprint.route('/api/registration', methods=['POST'])
def start_register():
    try:
        params = request.json
        session = db_session.create_session()
        nick_is_exist = session.query(User).filter(User.nickname == params['nickname']).first()
        if nick_is_exist is not None:
            return make_response(jsonify({'error': 'Nickname is exist'}), 400)
        email_is_exist = session.query(User).filter(User.email == params['email']).first()
        if email_is_exist is not None:
            return make_response(jsonify({'error': 'Email is exist'}), 400)

        if params['password'] != params['confirmPassword']:
            return make_response(jsonify({'error': 'Passwords not match'}), 400)

        if len(params['password']) < 6:
            return make_response(jsonify({'error': 'Password too short'}), 400)

        new_user = User()
        new_user.name = params['name']
        new_user.surname = params['surname']
        new_user.age = params['age']
        new_user.nickname = params['nickname']
        new_user.gender = params['gender']
        new_user.email = params['email']

        salt, key = make_password(params['password'])
        new_user.salt = salt
        new_user.password_hash = key

        new_user.token = generate_token()
        expires_at = (datetime.now(timezone.utc) + timedelta(seconds=TOKEN_LIVE_TIME_S))
        new_user.expires_at = int(expires_at.timestamp())

        session.add(new_user)
        session.commit()

        response = dict()
        response['token'] = new_user.token
        response['expiresIn'] = new_user.expires_at
        session.close()
        return make_response(response, 201)
    except KeyError:
        session.close()
        return make_response(jsonify({'error': 'Missing argument'}), 400)
    except Exception:
        session.close()
        return make_response(jsonify({'error': 'Something gone wrong'}), 400)


@blueprint.route('/api/login', methods=['POST'])
def start_login():
    try:
        params = request.json
        session = db_session.create_session()
        exist_user: User = session.query(User).filter(User.email == params['email']).first()

        if exist_user is None:
            return make_response(jsonify({'error': 'login or password incorrect'}), 403)

        salt = exist_user.salt
        password_hash = exist_user.password_hash
        is_valid_password = check_password(salt, params['password'], password_hash)

        if not is_valid_password:
            return make_response(jsonify({'error': 'login or password incorrect'}), 403)

        exist_user.token = generate_token()
        expires_at = (datetime.now(timezone.utc) + timedelta(seconds=TOKEN_LIVE_TIME_S))
        exist_user.expires_at = int(expires_at.timestamp())
        session.commit()

        response = dict()
        response['token'] = exist_user.token
        response['expiresIn'] = expires_at.astimezone().isoformat()
        session.close()
        return make_response(response, 200)
    except KeyError:
        session.close()
        return make_response(jsonify({'error': 'Missing argument'
                                      }), 400)
    except Exception:
        session.close()
        return make_response(jsonify({'error': 'Something gone wrong'}), 400)


@blueprint.route('/api/article', methods=['POST'])
def post_article():
    try:
        params = request.json
        token = request.headers['authorization']

        session = db_session.create_session()
        user = session.query(User).filter(User.token == token).first()

        if user is None:
            return make_response(jsonify({'error': 'Authorization failed'}), 403)

        if user.expires_at < datetime.now().timestamp():
            return make_response(jsonify({'error': 'Authorization failed'}), 403)

        title = params['title']
        content = params['content']
        image = params['image']
        template = params['template']
        created = datetime.now(timezone.utc)

        article = Article()
        article.title = title
        article.content = content
        article.image = image
        article.template = template
        article.author = user
        article.author_id = user.id
        article.date = int(created.timestamp())
        session.add(article)
        session.commit()

        response = dict()
        response['id'] = article.id
        response['title'] = article.title
        response['content'] = article.content
        response['date'] = created.astimezone().isoformat()
        response['image'] = article.image
        response['template'] = article.template
        response['author'] = user.to_json()
        session.close()
        return make_response(response, 200)
    except KeyError:
        session.close()
        return make_response(jsonify({'error': 'Missing argument'}), 400)
    except Exception:
        session.close()
        return make_response(jsonify({'error': 'Something gone wrong'}), 400)


@blueprint.route('/api/article/<article_id>', methods=['GET'])
def get_article(article_id):
    try:
        session = db_session.create_session()
        token = request.headers.get('authorization')
        user = session.query(User).filter(User.token == token).first()
        article = session.query(Article).filter(Article.id == article_id).first()

        if user is None:
            user_id = -1
        else:
            user_id = user.id

        if article is None:
            return make_response(jsonify({'error': 'Article does not exist'}), 404)

        response = article.to_json()
        response['is_liked'] = user_id in response['user_liked']

        session.close()
        return make_response(response, 200)
    except KeyError:
        session.close()
        return make_response(jsonify({'error': 'Missing argument'}), 400)
    except Exception:
        session.close()
        return make_response(jsonify({'error': 'Something gone wrong'}), 400)


@blueprint.route('/api/article/<article_id>/like', methods=['GET'])
def like_article(article_id):
    try:
        token = request.headers['authorization']
        session = db_session.create_session()
        user = session.query(User).filter(User.token == token).first()

        if user is None:
            return make_response(jsonify({'error': 'Authorization failed'}), 403)

        if user.expires_at < datetime.now().timestamp():
            return make_response(jsonify({'error': 'Authorization failed'}), 403)

        article = session.query(Article).filter(Article.id == article_id).first()
        if article is None:
            return make_response(jsonify({'error': 'Article does not exist'}), 404)

        like = session.query(Like).filter(Like.liker == user, Like.liked == article).first()
        if like is not None:
            return make_response(jsonify({'error': 'Already liked'}), 400)

        like = Like()
        like.liker = user
        like.liked = article
        like.liked_id = article.id
        like.liker_id = user.id
        session.add(like)
        session.commit()
        session.close()
        return make_response(jsonify({}), 200)
    except KeyError:
        session.close()
        return make_response(jsonify({'error': 'Missing argument'}), 400)
    except Exception:
        session.close()
        return make_response(jsonify({'error': 'Something gone wrong'}), 400)


@blueprint.route('/api/article/<article_id>/unlike', methods=['GET'])
def unlike_article(article_id):
    try:
        token = request.headers['authorization']
        session = db_session.create_session()
        user = session.query(User).filter(User.token == token).first()

        if user is None:
            return make_response(jsonify({'error': 'Authorization failed'}), 403)

        if user.expires_at < datetime.now().timestamp():
            return make_response(jsonify({'error': 'Authorization failed'}), 403)

        article = session.query(Article).filter(Article.id == article_id).first()
        if article is None:
            return make_response(jsonify({'error': 'Article does not exist'}), 404)

        like = session.query(Like).filter(Like.liker == user, Like.liked == article).first()
        if like is None:
            return make_response(jsonify({'error': 'Already unliked'}), 400)

        session.delete(like)
        session.commit()
        session.close()
        return make_response(jsonify({}), 200)
    except KeyError:
        session.close()
        return make_response(jsonify({'error': 'Missing argument'}), 400)
    except Exception:
        session.close()
        return make_response(jsonify({'error': 'Something gone wrong'}), 400)


@blueprint.route('/api/article', methods=['GET'])
def get_articles():
    try:
        params = request.args
        session = db_session.create_session()
        page = int(params.get('page'))
        limit = int(params.get('limit'))
        search = params.get('search')
        token = request.headers.get('authorization')
        user = session.query(User).filter(User.token == token).first()
        if user is None:
            user_id = -1
        else:
            user_id = user.id

        if search is None:
            articles = list(session.query(Article).all())
        else:
            articles = list(session.query(Article).filter(Article.title.ilike(f"%{search}%")).all())

        response = dict()
        total = len(articles)

        response['currentPage'] = page
        response['lastPage'] = total // limit
        response['perPage'] = limit
        response['data'] = []

        if len(articles) <= (page - 1) * limit:
            response['data'] = []
            response['total'] = 0
            session.close()
            return make_response(response, 200)

        articles_perf = articles[(page - 1) * limit: page * limit]
        for article in articles_perf:
            article: Article
            temp = article.get_short_desc()
            temp['is_liked'] = user_id in temp['user_liked']
            response['data'].append(temp)

        response['total'] = len(response['data'])
        session.close()
        return make_response(response, 200)

    except KeyError:
        session.close()
        return make_response(jsonify({'error': 'Missing argument'}), 400)
    except Exception:
        return make_response(jsonify({'error': 'Something gone wrong'}), 400)


@blueprint.route('/api/article/<article_id>', methods=['DELETE'])
def delete_article(article_id):
    try:
        params = request.args
        session = db_session.create_session()
        token = request.headers['authorization']
        user = session.query(User).filter(User.token == token).first()

        if user is None:
            return make_response(jsonify({'error': 'Authorizatino faile'}), 403)

        if user.expires_at < datetime.now().timestamp():
            return make_response(jsonify({'error': 'Authorization failed'}), 403)

        if not user.is_admin:
            return make_response(jsonify({'error': 'Access is denied'}), 403)

        article = session.query(Article).filter(Article.id == article_id).first()

        if article is None:
            return make_response(jsonify({'error': "Article is not exist"}), 404)

        session.delete(article)
        session.commit()
        session.close()
        return make_response(200)
    except KeyError:
        session.close()
        return make_response(jsonify({'error': 'Missing argument'}), 400)
    except Exception:
        return make_response(jsonify({'error': 'Something went wrong'}), 400)


@blueprint.route('/api/profile/liked', methods=['GET'])
def get_liked_articles():
    try:
        params = request.args
        session = db_session.create_session()
        page = int(params.get('page'))
        limit = int(params.get('limit'))
        search = params.get('search')
        token = request.headers['authorization']
        user = session.query(User).filter(User.token == token).first()

        if user is None:
            return make_response(jsonify({'error': 'Authorization failed'}), 403)

        if user.expires_at < datetime.now().timestamp():
            return make_response(jsonify({'error': 'Authorization failed'}), 403)
        if search is None:
            articles = list(session.query(Article).all())
        else:
            articles = list(session.query(Article).filter(Article.title == search).all())

        response = dict()
        total = len(articles)

        response['currentPage'] = page
        response['lastPage'] = total // limit
        response['perPage'] = limit
        response['data'] = []

        if len(articles) <= (page - 1) * limit:
            response['data'] = []
            response['total'] = 0
            session.close()
            return make_response(response, 200)

        articles_perf = articles[(page - 1) * limit: page * limit]
        for article in articles_perf:
            article: Article
            temp = article.get_short_desc()
            if user.id in temp['user_liked']:
                temp['is_liked'] = True
                response['data'].append(temp)

        response['total'] = len(response['data'])
        session.close()
        return make_response(response, 200)

    except KeyError:
        session.close()
        return make_response(jsonify({'error': 'Missing argument'}), 400)
    except Exception:
        return make_response(jsonify({'error': 'Something gone wrong'}), 400)


@blueprint.route('/api/map', methods=['POST'])
def post_point():
    try:
        params = request.json
        session = db_session.create_session()
        token = request.headers['authorization']
        user = session.query(User).filter(User.token == token).first()

        if user is None:
            return make_response(jsonify({'error': 'Authorization failed'}), 403)

        if user.expires_at < datetime.now().timestamp():
            return make_response(jsonify({'error': 'Authorization failed'}), 403)

        point = Point()

        point.title = params['title']
        point.icon = params['iconImageHref']
        point.address = params['address']
        point.pointX = params['pointX']
        point.pointY = params['pointY']
        point.types = params['types']
        point.images = dumps(params['images'])
        point.comment = params['comment']
        point.user_id = user.id
        session.add(point)
        session.commit()
        session.close()
        return make_response(jsonify({}), 200)

    except KeyError:
        session.close()
        return make_response(jsonify({'error': 'Missing argument'}), 400)
    except Exception:
        session.close()
        return make_response(jsonify({'error': 'Something gone wrong'}), 400)


@blueprint.route('/api/map', methods=['GET'])
def get_points():
    try:
        params = request.args
        session = db_session.create_session()
        types = params['types']
        all_includes = params['allIncludes'].lower() == 'true'
        is_accepted = params['isAccepted'].lower() == 'true'
        points = session.query(Point).filter(Point.is_accepted == is_accepted).all()
        types = json.loads(types)
        if all_includes:
            points_filtered = filter(
                lambda x: len(set(types).intersection(set(json.loads(x.types)))) >= len(types) > 0,
                points)
        else:
            points_filtered = filter(lambda x: len(set(types).intersection(set(json.loads(x.types)))) > 0,
                                     points)
        response = dict()
        response['points'] = []

        for point in points_filtered:
            point: Point
            response['points'].append(point.to_json())

        session.close()
        return make_response(response, 200)
    except KeyError:
        session.close()
        return make_response(jsonify({'error': 'Missing argument'}), 400)
    except Exception:
        session.close()
        return make_response(jsonify({'error': 'Something gone wrong'}), 400)


@blueprint.route('/api/map/<point_id>/', methods=['GET'])
def get_point(point_id):
    try:
        params = request.args
        session = db_session.create_session()
        is_accepted = params['isAccepted'].lower() == 'true'
        point = session.query(Point).filter(Point.is_accepted == is_accepted, Point.id == int(point_id)).first()
        if point is None:
            return make_response(jsonify({'error': 'Point not found'}), 403)

        response = point.to_json()

        session.close()
        return make_response(response, 200)
    except KeyError:
        session.close()
        return make_response(jsonify({'error': 'Missing argument'}), 400)
    except Exception:
        session.close()
        return make_response(jsonify({'error': 'Something gone wrong'}), 400)


@blueprint.route('/api/profile/favs', methods=['GET'])
def get_favorite_points():
    try:
        params = request.args
        session = db_session.create_session()
        page = int(params.get('page'))
        limit = int(params.get('limit'))
        search = params.get('search')
        token = request.headers['authorization']
        user = session.query(User).filter(User.token == token).first()

        types = params['types']
        all_includes = params['allIncludes'].lower() == 'true'
        is_accepted = params['isAccepted'].lower() == 'true'
        if search is None:
            points = session.query(Point).filter(Point.is_accepted == is_accepted).all()
        else:
            points = session.query(Point).filter(Point.is_accepted == is_accepted, Point.title == search).all()

        types = json.loads(types)
        if all_includes:
            points_filtered = filter(
                lambda x: len(set(types).intersection(set(json.loads(x.types)))) >= len(types) > 0,
                points)
        else:
            points_filtered = filter(lambda x: len(set(types).intersection(set(json.loads(x.types)))) > 0,
                                     points)

        total = len(points_filtered)

        response = dict()
        response['currentPage'] = page
        response['lastPage'] = total // limit
        response['perPage'] = limit
        response['points'] = []

        if total <= (page - 1) * limit:
            response['total'] = 0
            session.close()
            return make_response(response, 200)

        points_perf = points_filtered[(page - 1) * limit: page * limit]
        for point in points_perf:
            point: Point
            for favorite in user.favorites:
                if favorite.fav_point_id == point.id:
                    response['points'].append(point.to_json())

        session.close()
        return make_response(response, 200)
    except KeyError:
        session.close()
        return make_response(jsonify({'error': 'Missing argument'}), 400)
    except Exception:
        session.close()
        return make_response(jsonify({'error': 'Something gone wrong'}), 400)


@blueprint.route('/api/map/<id>', methods=['PUT'])
def put_point(id):
    try:
        params = request.json
        session = db_session.create_session()
        token = request.headers['authorization']
        user = session.query(User).filter(User.token == token).first()

        if user is None:
            return make_response(jsonify({'error': 'Authorization failed'}), 403)

        if user.expires_at < datetime.now().timestamp():
            return make_response(jsonify({'error': 'Authorization failed'}), 403)
        
        if not user.is_admin:
            return make_response(jsonify({'error': 'Access denied'}), 403)

        point = session.query(Point).filter(Point.id == id).first()

        if point is None:
            return make_response(jsonify({'error': 'Point not found'}), 404)
        
        creator = session.query(User).filter(User.id == point.user_id).first()
        if creator is None:
            creator = user
        
        notification = Notification()
        notification.user_id = creator.id
        notification.date = datetime.now().timestamp()
        notification.notification_type = 'accept'
        notification.obj_id = creator.id

        point.title = params['title']
        point.icon = params['iconImageHref']
        point.address = params['address']
        point.pointX = params['pointX']
        point.pointY = params['pointY']
        point.types = params['types']
        point.images = dumps(params['images'])
        point.comment = params['comment']
        point.is_accepted = True
        point.user.rate += 15
        session.add(notification)
        session.commit()
        session.close()
        return make_response(jsonify({}), 200)
    except KeyError:
        session.close()
        return make_response(jsonify({'error': 'Missing argument'}), 400)
    except Exception:
        session.close()
        return make_response(jsonify({'error': 'Something gone wrong'}), 400)


@blueprint.route('/api/map/<id>', methods=['DELETE'])
def delete_point(id):
    try:
        session = db_session.create_session()
        token = request.headers['authorization']
        user = session.query(User).filter(User.token == token).first()

        if user is None:
            return make_response(jsonify({'error': 'Authorization failed'}), 403)

        if user.expires_at < datetime.now().timestamp():
            return make_response(jsonify({'error': 'Authorization failed'}), 403)

        if not user.is_admin:
            return make_response(jsonify({'error': 'Access denied'}), 403)
        
        point = session.query(Point).filter(Point.id == id).first()

        if point is None:
            return make_response(jsonify({'error': 'Point not found'}), 404)
        
        creator = session.query(User).filter(User.id == point.user_id).first()
        if creator is None:
            creator = user

        notification = Notification()
        notification.user_id = creator.id
        notification.date = datetime.now().timestamp()
        notification.notification_type = 'decline'
        notification.obj_id = point.id


        session.add(notification)
        session.delete(point)
        session.commit()
        session.close()
        return make_response(jsonify({}), 200)
    except KeyError:
        session.close()
        return make_response(jsonify({'error': 'Missing argument'}), 400)
    except Exception:
        session.close()
        return make_response(jsonify({'error': 'Something gone wrong'}), 400)


@blueprint.route('/api/map/fav/<point_id>', methods=['GET'])
def set_favorite_point(point_id):
    try:
        token = request.headers['authorization']
        session = db_session.create_session()
        user = session.query(User).filter(User.token == token).first()

        if user is None:
            return make_response(jsonify({'error': 'Authorization failed'}), 403)

        if user.expires_at < datetime.now().timestamp():
            return make_response(jsonify({'error': 'Authorization failed'}), 403)

        point = session.query(Point).filter(Point.id == point_id).first()
        if point is None:
            return make_response(jsonify({'error': 'Point does not exist'}), 404)

        favorite = session.query(Favorite).filter(Favorite.fav_user == user, Favorite.fav_point == point).first()
        if favorite is not None:
            return make_response(jsonify({'error': 'Already set to favorite'}), 400)

        favorite = Favorite()
        favorite.fav_user = user
        favorite.fav_point = point
        favorite.fav_point_id = point.id
        favorite.fav_user_id = user.id
        session.add(favorite)
        session.commit()
        session.close()
        return make_response(jsonify({}), 200)
    except KeyError:
        session.close()
        return make_response(jsonify({'error': 'Missing argument'}), 400)
    except Exception:
        session.close()
        return make_response(jsonify({'error': 'Something gone wrong'}), 400)


@blueprint.route('/api/map/unfav/<point_id>', methods=['GET'])
def unset_favorite_point(point_id):
    try:
        token = request.headers['authorization']
        session = db_session.create_session()
        user = session.query(User).filter(User.token == token).first()

        if user is None:
            return make_response(jsonify({'error': 'Authorization failed'}), 403)

        if user.expires_at < datetime.now().timestamp():
            return make_response(jsonify({'error': 'Authorization failed'}), 403)

        point = session.query(Point).filter(Point.id == point_id).first()
        if point is None:
            return make_response(jsonify({'error': 'Point does not exist'}), 404)

        favorite = session.query(Favorite).filter(Favorite.fav_user == user, Favorite.fav_point == point).first()
        if favorite is None:
            return make_response(jsonify({'error': 'Already removed from favorite'}), 400)

        session.delete(favorite)
        session.commit()
        session.close()
        return make_response(jsonify({}), 200)
    except KeyError:
        session.close()
        return make_response(jsonify({'error': 'Missing argument'}), 400)
    except Exception:
        session.close()
        return make_response(jsonify({'error': 'Something gone wrong'}), 400)


@blueprint.route('/api/images', methods=['POST'])
def upload_file():
    session = db_session.create_session()
    token = request.headers['authorization']
    user = session.query(User).filter(User.token == token).first()

    if user is None:
        session.close()
        return make_response(jsonify({'error': 'Authorization failed'}), 403)

    if user.expires_at < datetime.now().timestamp():
        session.close()
        return make_response(jsonify({'error': 'Authorization failed'}), 403)
    session.close()
    try:
        if 'file' not in request.files:
            return make_response(jsonify({'error': 'Empty requset. File not found'}), 400)
        file = request.files['file']
        if file.filename == '':
            return make_response(jsonify({'error': 'Empty filename.'}), 400)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filename = filename.split('.')
            filename[0] = filename[0] + str(int(time.time()))
            filename = '.'.join(filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            response = dict()
            response['link'] = DOMEN + 'api/images/' + filename
            return make_response(response, 200)
        return make_response(jsonify({'error': 'Something gone wrong'}), 400)
    except Exception:
        return make_response(jsonify({'error': 'Something gone wrong'}), 400)


@blueprint.route('/api/images/<image>', methods=['GET'])
def download_file(image):
    directory = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
    try:
        return send_from_directory(directory=directory, path=image)
    except Exception:
        return make_response(jsonify({'error': 'Something gone wrong'}), 400)


@blueprint.route('/api/profile', methods=['GET'])
def get_profile():
    try:
        params = request.args
        token = request.headers['authorization']
        session = db_session.create_session()
        user = session.query(User).filter(User.token == token).first()

        if user is None:
            return make_response(jsonify({'error': 'Authorization failed'}), 403)

        if user.expires_at < datetime.now().timestamp():
            return make_response(jsonify({'error': 'Authorization failed'}), 403)

        user_id = params.get('id', None)
        if user_id is None:
            user_id = user.id

        user = session.query(User).filter(User.id == user_id).first()
        if user is None:
            return make_response(jsonify({'error': 'User not found'}), 404)

        response = user.to_json()
        return make_response(response, 200)

    except KeyError:
        return make_response(jsonify({'error': 'Missing argument'}), 400)
    except Exception:
        return make_response(jsonify({'error': 'Something gone wrong'}), 400)


@blueprint.route('/api/profile/<user_id>', methods=['GET'])
def get_profile_by_id(user_id):
    try:
        params = request.args
        token = request.headers['authorization']
        session = db_session.create_session()
        user = session.query(User).filter(User.token == token).first()

        if user is None:
            return make_response(jsonify({'error': 'Authorization failed'}), 403)

        if user.expires_at < datetime.now().timestamp():
            return make_response(jsonify({'error': 'Authorization failed'}), 403)

        user = session.query(User).filter(User.id == user_id).first()

        if (user == None):
            return make_response(jsonify({'error': 'User not found'}), 404)

        response = user.to_json()
        return make_response(response, 200)

    except KeyError:
        return make_response(jsonify({'error': 'Missing argument'}), 400)
    except Exception:
        return make_response(jsonify({'error': 'Something went wrong'}), 400)


@blueprint.route('/api/profile', methods=['PUT'])
def put_profile():
    try:
        params = request.args
        token = request.headers['authorization']
        session = db_session.create_session()
        user = session.query(User).filter(User.token == token).first()

        if user is None:
            return make_response(jsonify({'error': 'Authorization failed'}), 403)

        if user.expires_at < datetime.now().timestamp():
            return make_response(jsonify({'error': 'Authorization failed'}), 403)

        if 'name' in params:
            user.name = params['name']
        if 'age' in params:
            user.age = params['age']
        if 'surname' in params:
            user.surname = params['surname']
        if 'nickname' in params:
            user.nickname = params['nickname']
        if 'gender' in params:
            user.gender = params['gender']
        if 'email' in params:
            user.email = params['email']
        if 'avatar' in params:
            user.avatar = params['avatar']

        session.commit()
        response = user.to_json()
        session.close()
        return make_response(response, 200)

    except KeyError:
        session.close()
        return make_response(jsonify({'error': 'Missing argument'}), 400)
    except Exception:
        session.close()
        return make_response(jsonify({'error': 'Something gone wrong'}), 400)


@blueprint.route('/api/profile/subscribe/<user_id>/', methods=['POST'])
def subscribe_to_user(user_id):
    try:
        token = request.headers['authorization']
        session = db_session.create_session()
        user = session.query(User).filter(User.token == token).first()

        if user is None:
            return make_response(jsonify({'error': 'Authorization failed'}), 403)

        if user.expires_at < datetime.now().timestamp():
            return make_response(jsonify({'error': 'Authorization failed'}), 403)

        user_to_subscribe = session.query(User).filter(User.id == int(user_id)).first()
        if user_to_subscribe is None:
            return make_response(jsonify({'error': 'User to subscribe does not exist'}), 404)

        subscription = session.query(Subscribe).filter(Subscribe.subscribed_to_user == user_to_subscribe,
                                                       Subscribe.subscriber_user == user).first()
        if subscription is not None:
            return make_response(jsonify({'error': 'Already subscribed'}), 400)
        
        notification = Notification()
        notification.user_id = user_to_subscribe.id
        notification.date = datetime.now().timestamp()
        notification.notification_type = 'subscribe'
        notification.obj_id = user.id


        subscribe = Subscribe()
        subscribe.subscriber_user = user
        subscribe.subscriber_user_id = user.id
        subscribe.subscribed_to_user = user_to_subscribe
        subscribe.subscribed_to_user_id = user_to_subscribe.id
        session.add(subscribe)
        session.add(notification)
        session.commit()
        session.close()
        return make_response(jsonify({}), 200)
    except KeyError:
        session.close()
        return make_response(jsonify({'error': 'Missing argument'}), 400)
    except Exception:
        session.close()
        return make_response(jsonify({'error': 'Something gone wrong'}), 400)


@blueprint.route('/api/profile/subscribe', methods=['GET'])
def get_subscriptions():
    try:
        session = db_session.create_session()
        token = request.headers['authorization']
        user = session.query(User).filter(User.token == token).first()

        if user is None:
            return make_response(jsonify({'error': 'Authorization failed'}), 403)

        if user.expires_at < datetime.now().timestamp():
            return make_response(jsonify({'error': 'Authorization failed'}), 403)

        subscriptions = session.query(Subscribe).filter(Subscribe.subscriber_user == user).all()

        if subscriptions is None:
            return make_response(jsonify({'error': 'Nobody subscribed'}), 403)

        response = dict()
        response['users'] = []

        for sub in subscriptions:
            sub_user = sub.subscribed_to_user
            sub_user: User
            response['users'].append(sub_user.to_json())

        session.close()
        return make_response(response, 200)

    except KeyError:
        session.close()
        return make_response(jsonify({'error': 'Missing argument'}), 400)
    except Exception:
        return make_response(jsonify({'error': 'Something gone wrong'}), 400)


blueprint.route('/api/notification', methods=['GET'])
def get_notification():
    try:
        token = request.headers['authorization']
        session = db_session.create_session()
        user = session.query(User).filter(User.token == token).first()

        if user is None:
            session.close()
            return make_response(jsonify({'error': 'Authorization failed'}), 403)
        if user.expires_at > datetime.now().timestamp():
            session.close()
            return make_response(jsonify({'error': 'Authorization failde'}), 403)
        
        notifications = list(session.query(Notification).filter(notification.user_id == user.id).all())

        if notifications.count == 0:
            session.close()
            return make_response(jsonify({'error': 'Notifications not found'}), 404)
        notification = notifications[-1]

        response = dict()
        response['user'] = {user.id, user.avatar, user.name, user.surname}
        response['date'] = datetime.fromtimestamp(notification.date)
        response['type'] = notification.notification_type
        if notification.notification_type == 'subscribe':
            sub_user = session.query(User).filter(User.id == notification.obj_id).first()
            response['data'] = sub_user.to_json()
        else:
            point = session.query(Point).filter(Point.id == notification.obj_id).first()
            response['data'] = point.to_json()
        
        session.delete(notification)
        session.commit()
        session.close()
        return make_response(response, 200)
    except KeyError:
        session.close()
        return make_response(jsonify({'error': 'Missing argument'}), 400)
    except Exception:
        session.close()
        return make_response(jsonify({'error': 'Something gone wrong'}), 400)


app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
app.register_blueprint(blueprint)
db_session.global_init(DB_CONN_STR)
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5243, debug=True)