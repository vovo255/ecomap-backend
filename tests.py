from requests import post
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


if __name__ == '__main__':
    test_login()
