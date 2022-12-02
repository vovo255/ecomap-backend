import hashlib
import os


def make_password(password):
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt.hex(), key.hex()


def check_password(salt, password, key):
    salt = bytes.fromhex(salt)
    key = bytes.fromhex(key)
    new_key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return new_key == key


def generate_token():
    return os.urandom(32).hex()


if __name__ == '__main__':
    print(generate_token())
    salt, pas = make_password('test')
    print(salt, pas)
    print(check_password(salt, 'test', pas))
