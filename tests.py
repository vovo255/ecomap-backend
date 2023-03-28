from requests import post, get
from pprint import pprint
from settings import DOMEN

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

    resp = post(DOMEN + 'api/registration', json=test_1_query)

    print(resp.status_code)
    pprint(resp.json())


def test_login():
    test_2_query = dict()
    test_2_query['email'] = 'test@test.ru'
    test_2_query['password'] = 'qwerty12345'

    resp = post(DOMEN + 'api/login', json=test_2_query)

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


if __name__ == '__main__':
    #test_registration()
    #test_login()
    #test_post_article('7d3c7d21c652f4bd24a53d644915fe095081d5b82ad674d7f23b48a88c730bec')
    #test_get_article('7d3c7d21c652f4bd24a53d644915fe095081d5b82ad674d7f23b48a88c730bec')
    #test_like('7d3c7d21c652f4bd24a53d644915fe095081d5b82ad674d7f23b48a88c730bec')
    #test_unlike('7d3c7d21c652f4bd24a53d644915fe095081d5b82ad674d7f23b48a88c730bec')
    test_get_articles('7d3c7d21c652f4bd24a53d644915fe095081d5b82ad674d7f23b48a88c730bec')
    test_get_articles('7d3c7d21c652f4bd24a53d644915fe095081d5b82ad674d7f23b48a88c730bec')
