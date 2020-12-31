# -*- coding: utf-8 -*-
#!/usr/bin/python3
"""
:module:    gm_encrypt
:class:     GmEncrypt

Simple encryption methods

:author:    PQ <pq_rfw @ pm.me>
"""
import inspect
import json
from os import path
from pprint import pprint as pp

from cryptography.fernet import Fernet
from tornado.options import define, options

from gm_functions import GmFunctions
from gm_reference import GmReference

GF = GmFunctions()
GR = GmReference()

class GmEncrypt(object):
    """
    - Create a tag and an encryption key
    - Encrypt/decrypt texts using a key
    """
    def __init__(self):
        """ Initialize GmEncrypt object
        """
        pass

    def __repr__(self):
        """ Provide description of the class

            TODO Update this when code has settled down
        """
        sep = GR.LF + GR.LF + GR.LINE + GR.LF + GR.LF
        methods = "".join(
            [GR.LF  + "*************************",
             GR.LF  + "**  GmEncrypt Methods  **",
             GR.LF  + "*************************",
             sep, "GmEncrypt/0 => None" + GR.LF_TAB, inspect.getdoc(self.__init__),
             sep, "set_key/0 => JSON" + GR.LF,
             "set_key/1 => JSON" + GR.LF_TAB, inspect.getdoc(self.set_key),
             sep, "encrypt_data/2 => string" + GR.LF_TAB, inspect.getdoc(self.encrypt_data),
             sep, "decrypt_data/2 => string" + GR.LF_TAB, inspect.getdoc(self.decrypt_data), sep
            ])
        return methods

    def set_key(self) -> str:
        """ Create a key for use with Fernet encryption.

        Returns:
            bytes: encryption key
        """
        encrypt_key = Fernet.generate_key()
        return encrypt_key

    @classmethod
    def encrypt_data(cls, p_plaintext: str, p_key: bytes) -> str:
        """ Return encrypted version of the plaintext

        Args:
            p_plaintext (string): data to be encrypted
            p_key (bytes):  encryption key to use

        Returns:
            string: encrypted version of data
        """
        cipher_suite = Fernet(p_key)
        encoded_bytes = cipher_suite.encrypt(bytes(p_plaintext, 'utf-8'))
        return encoded_bytes.decode("utf-8")

    @classmethod
    def decrypt_data(cls, p_encrypted, p_key):
        """ Return decrypted version of the encrypted data.

        Args:
            p_encrypted (string):  data encrypted using GmEncrypt.encrypt_data()
            p_key (string): same key that was used to encrypt it

        Returns:
            string: decrypted value
        """
        cipher_suite = Fernet(p_key)
        decoded_str = cipher_suite.decrypt(bytes(p_encrypted, 'utf-8'))
        decoded_str = decoded_str.decode("utf-8")
        return decoded_str
