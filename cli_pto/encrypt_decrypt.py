import random
import string

from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Util.Padding import pad, unpad


BLOCK_SIZE = 32

class EncryptDecrypt:
    def __init__(self, user, password):
        self.user = user
        self.password = password

    def __generate_key(self):
        user = self.user
        password = self.password

        random.seed(user)
        salt = ''.join(random.choice(string.ascii_lowercase) for i in range(32))

        return PBKDF2(password, salt, 16, 1000, None)

    def encrypt_text(self, text):
        cipher = AES.new(self.__generate_key(), AES.MODE_ECB)
        msg_to_encrypt = bytes(text, 'utf-8')
        return cipher.encrypt(pad(msg_to_encrypt, BLOCK_SIZE))

    def decrypt_text(self, text):
        if text == "":
            return ""
        else:
            cipher = AES.new(self.__generate_key(), AES.MODE_ECB)
            try:
                return unpad(cipher.decrypt(text), BLOCK_SIZE).decode('utf-8')
            except:
                return 'Wrong username or password'