from requests import post, get, options
from pprint import pprint
from settings import DOMEN


def test_registration():
    test_1_query = dict()
    test_1_query['name'] = 'Админ'
    test_1_query['surname'] = 'Админ'
    test_1_query['age'] = 19
    test_1_query['nickname'] = 'admin'
    test_1_query['gender'] = 1
    test_1_query['email'] = 'admin@mail.ru'
    test_1_query['password'] = '123123'
    test_1_query['confirmPassword'] = '123123'

    # test_1_query['name'] = 'Владимир'
    # test_1_query['surname'] = 'Алексеев'
    # test_1_query['age'] = 19
    # test_1_query['nickname'] = 'vovo255'
    # test_1_query['gender'] = 1
    # test_1_query['email'] = 'it@vladimirva.ru'
    # test_1_query['password'] = '123123'
    # test_1_query['confirmPassword'] = '123123'

    resp = post(DOMEN + 'api/registration', json=test_1_query)

    print(resp.status_code)
    pprint(resp.json())


def test_login():
    test_2_query = dict()
    # test_2_query['email'] = 'admin@mail.ru'
    # test_2_query['password'] = '123123'

    test_2_query['email'] = 'it@vladimirva.ru'
    test_2_query['password'] = '123123'

    resp = post(DOMEN + 'api/login', json=test_2_query)

    print(resp.status_code)
    pprint(resp.json())
    return resp.json()['token']


def test_post_article(token):
    test_3_query = dict()
    test_3_query['title'] = 'Статья об экологии 4'
    test_3_query['content'] = 'Какая-то оч длинная строка'
    test_3_query['image'] = 'https://photo.com/photo.jpg'
    test_3_query['template'] = 1

    headers = dict()
    headers['authorization'] = token

    resp = post(DOMEN + 'api/article', json=test_3_query, headers=headers)

    print(resp.status_code)
    pprint(resp.json())


def test_get_article(token):
    headers = dict()
    headers['authorization'] = token

    resp = get(DOMEN + 'api/article/1', headers=headers)

    print(resp.status_code)
    pprint(resp.json())


def test_like(token):
    headers = dict()
    headers['authorization'] = token

    resp = get(DOMEN + 'api/article/1/like', headers=headers)

    print(resp.status_code)
    pprint(resp.json())


def test_unlike(token):
    headers = dict()
    headers['authorization'] = token

    resp = get(DOMEN + '/api/article/1/unlike', headers=headers)

    print(resp.status_code)
    pprint(resp.json())


def test_get_articles(token):
    headers = dict()
    headers['authorization'] = token

    resp = get(DOMEN + 'api/article?page=2&limit=2', headers=headers)

    print(resp.status_code)
    pprint(resp.json())


def test_profile(token):
    headers = dict()
    headers['authorization'] = token

    resp = get(DOMEN + 'api/profile', headers=headers)

    print(resp.status_code)
    pprint(resp.json())


def test_subscribe_to_user(token, user_id):
    headers = dict()
    headers['authorization'] = token

    resp = post(DOMEN + '/api/profile/subscribe/' + user_id, headers=headers)

    print(resp.status_code)
    pprint(resp.json())


def test_subscribe(user_id):
    headers = dict()

    resp = get(DOMEN + '/api/profile/subscribe/' + user_id, headers=headers)

    print(resp.status_code)
    pprint(resp.json())


def test_subscribers(user_id):
    headers = dict()

    resp = get(DOMEN + '/api/profile/subscribers/' + user_id, headers=headers)

    print(resp.status_code)
    pprint(resp.json())


def test_post_point(token):
    test_6_query = dict()
    test_6_query['title'] = 'Точка 3'
    test_6_query['iconImageHref'] = 'Строка-ссылка-на-изображение'
    test_6_query['address'] = "Строка с адресом, сделать поле опциональным, потому что мб не надо будет"
    test_6_query['pointX'] = 40.29
    test_6_query['pointY'] = 40.29
    test_6_query['types'] = [1]
    test_6_query['images'] = ["Массив с ссылками на изображения"]
    test_6_query['comment'] = 'Комментарий'

    headers = dict()
    headers['authorization'] = token

    resp = post(DOMEN + 'api/map', json=test_6_query, headers=headers)

    print(resp.status_code)
    pprint(resp.json())


def test_get_points(token):
    headers = dict()
    headers['authorization'] = token

    params = dict()
    params['types'] = '[1, 2, 3, 4]'
    params['allIncludes'] = False
    params['isAccepted'] = False
    resp = get(DOMEN + 'api/map', headers=headers, params=params)

    print(resp.status_code)
    pprint(resp.json())


if __name__ == '__main__':
    # test_registration()
    # test_login()
    # test_post_article('7d3c7d21c652f4bd24a53d644915fe095081d5b82ad674d7f23b48a88c730bec')
    # test_get_article('7d3c7d21c652f4bd24a53d644915fe095081d5b82ad674d7f23b48a88c730bec')
    # test_like('7d3c7d21c652f4bd24a53d644915fe095081d5b82ad674d7f23b48a88c730bec')
    # test_unlike('7d3c7d21c652f4bd24a53d644915fe095081d5b82ad674d7f23b48a88c730bec')
    # test_get_articles('7d3c7d21c652f4bd24a53d644915fe095081d5b82ad674d7f23b48a88c730bec')
    # test_get_articles('7d3c7d21c652f4bd24a53d644915fe095081d5b82ad674d7f23b48a88c730bec')
    # test_post_point('7141ec0c35c7778ff8bfbfd9cd9bca794f924445e014c759bc5cce8e381652cd')
    # test_get_points('7141ec0c35c7778ff8bfbfd9cd9bca794f924445e014c759bc5cce8e381652cd')
    # test_profile('d0d3ae15dcc228318ee490ca462011aa21b58ea0562cfd10bb43ba02132e7425')
    test_subscribe_to_user(test_login(), 1)
    test_subscribers(1)
