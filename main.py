import time
from flask import send_from_directory, Response
import flask
from flask import Flask, jsonify, request, make_response
from data import db_session
from datetime import datetime, timedelta, timezone
from data.table import User, Article, Like, Point
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
        new_user.expires_at = expires_at.astimezone().isoformat()

        session.add(new_user)
        session.commit()

        response = dict()
        response['token'] = new_user.token
        response['expiresIn'] = new_user.expires_at
        session.close()

        return make_response(response, 201)

    except KeyError:
        return make_response(jsonify({'error': 'Missing argument'}), 400)
    except Exception as e:
        traceback.print_exc()
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
        return make_response(jsonify({'error': 'Missing argument'
                                      }), 400)
    except Exception as e:
        return make_response(jsonify({'error': 'Something gone wrong'}), 400)


@blueprint.route('/api/article', methods=['POST'])
def post_article():
    try:
        params = request.json
        token = request.headers['authorization']

        session = db_session.create_session()
        user = session.query(User).filter(User.token == token).first()

        if user is None:
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
        print(article.to_json())
        session.close()

        return make_response(response, 200)

    except KeyError:
        return make_response(jsonify({'error': 'Missing argument'}), 400)
    except Exception as e:
        traceback.print_exc()
        return make_response(jsonify({'error': 'Something gone wrong'}), 400)


@blueprint.route('/api/article/<article_id>', methods=['GET'])
def get_article(article_id):
    try:
        token = request.headers['authorization']
        session = db_session.create_session()
        user = session.query(User).filter(User.token == token).first()

        if user is None:
            if user is None:
                return make_response(jsonify({'error': 'Authorization failed'}), 403)

        if user.expires_at < datetime.now().timestamp():
            return make_response(jsonify({'error': 'Authorization failed'}), 403)

        article = session.query(Article).filter(Article.id == article_id).first()
        if article is None:
            return make_response(jsonify({'error': 'Article does not exist'}), 404)

        response = article.to_json()
        session.close()
        return make_response(response, 200)

    except KeyError:
        return make_response(jsonify({'error': 'Missing argument'}), 400)
    except Exception as e:
        traceback.print_exc()
        return make_response(jsonify({'error': 'Something gone wrong'}), 400)


@blueprint.route('/api/article/<article_id>/like', methods=['GET'])
def like_article(article_id):
    try:
        token = request.headers['authorization']
        session = db_session.create_session()
        user = session.query(User).filter(User.token == token).first()

        if user is None:
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
        return make_response(jsonify({'error': 'Missing argument'}), 400)
    except Exception as e:
        traceback.print_exc()
        return make_response(jsonify({'error': 'Something gone wrong'}), 400)


@blueprint.route('/api/article/<article_id>/unlike', methods=['GET'])
def unlike_article(article_id):
    try:
        token = request.headers['authorization']
        session = db_session.create_session()
        user = session.query(User).filter(User.token == token).first()

        if user is None:
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
        return make_response(jsonify({'error': 'Missing argument'}), 400)
    except Exception as e:
        traceback.print_exc()
        return make_response(jsonify({'error': 'Something gone wrong'}), 400)


@blueprint.route('/api/article', methods=['GET'])
def get_articles():
    try:
        params = request.args
        token = request.headers['authorization']

        session = db_session.create_session()
        user = session.query(User).filter(User.token == token).first()

        if user is None:
            if user is None:
                return make_response(jsonify({'error': 'Authorization failed'}), 403)

        if user.expires_at < datetime.now().timestamp():
            return make_response(jsonify({'error': 'Authorization failed'}), 403)

        page = int(params.get('page'))
        limit = int(params.get('limit'))
        search = params.get('search')

        if search is None:
            articles = list(session.query(Article).all())
        else:
            articles = list(session.query(Article).filter(Article.title == search).all())

        articles_perf = list()
        response = dict()
        total = len(articles)

        response['currentPage'] = page
        response['lastPage'] = total // limit  # + (1 if total - total // limit > 0 else 0) TODO: Wtf?
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
            response['data'].append(article.get_short_desc())

        response['total'] = len(response['data'])

        return make_response(response, 200)

    except KeyError:
        return make_response(jsonify({'error': 'Missing argument'}), 400)
    except Exception as e:
        traceback.print_exc()
        return make_response(jsonify({'error': 'Something gone wrong'}), 400)


@blueprint.route('/api/map', methods=['POST'])
def post_point():
    try:
        params = request.json
        token = request.headers['authorization']

        session = db_session.create_session()
        user = session.query(User).filter(User.token == token).first()

        if user is None:
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
        point._type = params['type']
        point.images = dumps(params['images'])
        point.comment = params['comment']
        session.add(point)
        session.commit()
        session.close()
        return make_response(jsonify({}), 200)

    except KeyError:
        return make_response(jsonify({'error': 'Missing argument'}), 400)
    except Exception as e:
        traceback.print_exc()
        return make_response(jsonify({'error': 'Something gone wrong'}), 400)


@blueprint.route('/api/map', methods=['GET'])
def get_points():
    try:
        params = request.args
        token = request.headers['authorization']
        session = db_session.create_session()
        user = session.query(User).filter(User.token == token).first()

        if user is None:
            if user is None:
                return make_response(jsonify({'error': 'Authorization failed'}), 403)

        if user.expires_at < datetime.now().timestamp():
            return make_response(jsonify({'error': 'Authorization failed'}), 403)

        _type = params.get('type')
        points = session.query(Point).filter(Point._type == _type).all()
        response = dict()
        response['points'] = []

        for point in points:
            point: Point
            response['points'].append(point.to_json())

        session.close()

        return make_response(response, 200)

    except KeyError:
        return make_response(jsonify({'error': 'Missing argument'}), 400)
    except Exception as e:
        traceback.print_exc()
        return make_response(jsonify({'error': 'Something gone wrong'}), 400)


@blueprint.route('/api/images', methods=['POST'])
def upload_file():
    token = request.headers['authorization']
    session = db_session.create_session()
    user = session.query(User).filter(User.token == token).first()

    if user is None:
        if user is None:
            return make_response(jsonify({'error': 'Authorization failed'}), 403)

    if user.expires_at < datetime.now().timestamp():
        return make_response(jsonify({'error': 'Authorization failed'}), 403)
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
    except Exception as e:
        traceback.print_exc()
        return make_response(jsonify({'error': 'Something gone wrong'}), 400)


@blueprint.route('/api/images/<image>', methods=['GET'])
def download_file(image):
    token = request.headers['authorization']
    session = db_session.create_session()
    user = session.query(User).filter(User.token == token).first()

    if user is None:
        if user is None:
            return make_response(jsonify({'error': 'Authorization failed'}), 403)

    if user.expires_at < datetime.now().timestamp():
        return make_response(jsonify({'error': 'Authorization failed'}), 403)

    directory = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])

    try:
        return send_from_directory(directory=directory, path=image)
    except Exception as e:
        traceback.print_exc()
        return make_response(jsonify({'error': 'Something gone wrong'}), 400)


if __name__ == '__main__':
    app = Flask(__name__)
    CORS(app)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
    app.register_blueprint(blueprint)
    db_session.global_init(DB_CONN_STR)
    app.run(host='0.0.0.0', port=5243, debug=True)
