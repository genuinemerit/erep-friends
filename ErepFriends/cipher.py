# coding: utf-8     # noqa: E902
#!/usr/bin/python3  # noqa: E265

"""
Basic encryption methods.

Module:    cipher
Class:     Cipher
Author:    PQ <pq_rfw @ pm.me>
"""
from pprint import pprint as pp  # noqa: F401

from cryptography.fernet import Fernet


class Cipher(object):
    """Generic methods to encrypt/decrypt a string."""

    @classmethod
    def set_key(cls) -> bytes:
        """Create a key for use with Fernet encryption.

        Returns:
            bytes: encryption key
        """
        encrypt_key = Fernet.generate_key()
        return encrypt_key

    @classmethod
    def encrypt(cls, p_plaintext: str, p_key: bytes) -> str:
        """Return encrypted version of the plaintext.

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
    def decrypt(cls, p_encrypted: str, p_key: str) -> str:
        """Return decrypted version of the encrypted data.

        Args:
            p_encrypted (string):  data encrypted using Cipher.encrypt_data()
            p_key (string): same key that was used to encrypt it

        Returns:
            string: decrypted value
        """
        cipher_suite = Fernet(p_key)
        decoded_str = cipher_suite.decrypt(bytes(p_encrypted, 'utf-8'))
        decoded_str = decoded_str.decode("utf-8")
        return decoded_str
