import flask
from flask import Flask, jsonify, request, make_response
from data import db_session
from datetime import datetime, timedelta, timezone
from data.table import User, Article
from user_help import check_password, make_password, generate_token
from settings import DB_CONN_STR, TOKEN_LIVE_TIME_S
import traceback

blueprint = flask.Blueprint('main_api', __name__,
                            template_folder='api_templates')


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
        response['date'] =  created.astimezone().isoformat()
        response['image'] = article.image
        response['template'] = article.template
        response['author'] = user.to_json()
        session.close()

        return make_response(response, 200)

    except KeyError:
        return make_response(jsonify({'error': 'Missing argument'}), 400)
    except Exception as e:
        traceback.print_exc()
        return make_response(jsonify({'error': 'Something gone wrong'}), 400)


if __name__ == '__main__':
    app = Flask(__name__)
    app.register_blueprint(blueprint)
    db_session.global_init(DB_CONN_STR)
    app.run(host='0.0.0.0', port=8080, debug=True)
