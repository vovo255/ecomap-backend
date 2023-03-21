from requests import post, get
from pprint import pprint


def test_registration():
    test_1_query = dict()
    test_1_query['name'] = 'Петя'
    test_1_query['surname'] = 'Смирнов'
    test_1_query['age'] = 43
    test_1_query['nickname'] = 'PeSmi'
    test_1_query['gender'] = 1
    test_1_query['email'] = 'test@test.ru'
    test_1_query['password'] = 'qwerty12345'
    test_1_query['confirmPassword'] = 'qwerty12345'

    resp = post('http://127.0.0.1:8080/api/registration', json=test_1_query)

    print(resp.status_code)
    pprint(resp.json())


def test_login():
    test_2_query = dict()
    test_2_query['email'] = 'test@test.ru'
    test_2_query['password'] = 'qwerty12345'

    resp = post('http://127.0.0.1:8080/api/login', json=test_2_query)

    print(resp.status_code)
    pprint(resp.json())


def test_post_article(token):
    test_3_query = dict()
    test_3_query['title'] = 'Статья об экологии 4'
    test_3_query['content'] = 'Какая-то оч длинная строка'
    test_3_query['image'] = 'https://photo.com/photo.jpg'
    test_3_query['template'] = 1

    headers = dict()
    headers['authorization'] = token

    resp = post('http://127.0.0.1:8080/api/article', json=test_3_query, headers=headers)

    print(resp.status_code)
    pprint(resp.json())


def test_get_article(token):
    headers = dict()
    headers['authorization'] = token

    resp = get('http://127.0.0.1:8080/api/article/4', headers=headers)

    print(resp.status_code)
    pprint(resp.json())


def test_like(token):
    headers = dict()
    headers['authorization'] = token

    resp = get('http://127.0.0.1:8080/api/article/3/like', headers=headers)

    print(resp.status_code)
    pprint(resp.json())


if __name__ == '__main__':
    # test_registration()
    # test_login()
    # test_post_article('17a2403d9ce62d6f957eea19b527530b96a6692706916fc94bdb097ab2af49ca')
    #test_get_article('17a2403d9ce62d6f957eea19b527530b96a6692706916fc94bdb097ab2af49ca')
    test_like('17a2403d9ce62d6f957eea19b527530b96a6692706916fc94bdb097ab2af49ca')
