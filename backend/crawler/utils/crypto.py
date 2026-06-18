"""
加密工具模块 - AES-256-GCM加密
"""
import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag


class AESCipher:
    def __init__(self, key: str):
        if len(key) != 32:
            raise ValueError("加密密钥必须是32字节（256位）")
        self.key = key.encode('utf-8')
        self.aesgcm = AESGCM(self.key)
    
    def encrypt(self, plaintext: str) -> str:
        nonce = os.urandom(12)
        ciphertext = self.aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
        encrypted = nonce + ciphertext
        return base64.b64encode(encrypted).decode('utf-8')
    
    def decrypt(self, encrypted_text: str) -> str:
        try:
            encrypted = base64.b64decode(encrypted_text.encode('utf-8'))
            nonce = encrypted[:12]
            ciphertext = encrypted[12:]
            plaintext = self.aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext.decode('utf-8')
        except InvalidTag:
            raise ValueError("解密失败：密钥不匹配或数据被篡改")
        except Exception as e:
            raise ValueError(f"解密失败：{str(e)}")


def get_cipher() -> AESCipher:
    from config import settings
    key = settings.crawler_encryption_key
    if not key or len(key) != 32:
        raise ValueError("请在.env中配置CRAWLER_ENCRYPTION_KEY（32字节）")
    return AESCipher(key)
