# -*- coding: utf-8 -*-
"""
加密工具模块
用于密码的加密和解密
"""

import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os

class CryptoManager:
    """加密管理器"""

    def __init__(self, password=None):
        """
        初始化加密管理器

        Args:
            password: 加密密码，如果为None则使用默认密码
        """
        if password is None:
            # 使用程序相关的固定密钥
            password = "forum_assistant_2025_secret_key"

        self.password = password.encode()
        self._generate_key()

    def _generate_key(self):
        """生成加密密钥"""
        # 使用PBKDF2派生密钥
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'forum_assistant_salt',  # �定的salt
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.password))
        self.cipher = Fernet(key)

    def encrypt(self, data):
        """
        加密数据

        Args:
            data: 要加密的字符串

        Returns:
            加密后的base64字符串
        """
        if isinstance(data, str):
            data = data.encode('utf-8')

        encrypted_data = self.cipher.encrypt(data)
        return base64.b64encode(encrypted_data).decode('utf-8')

    def decrypt(self, encrypted_data):
        """
        解密数据

        Args:
            encrypted_data: 加密的base64字符串

        Returns:
            解密后的字符串
        """
        try:
            if isinstance(encrypted_data, str):
                encrypted_data = encrypted_data.encode('utf-8')

            encrypted_data = base64.b64decode(encrypted_data)
            decrypted_data = self.cipher.decrypt(encrypted_data)
            return decrypted_data.decode('utf-8')
        except Exception:
            # 解密失败返回空字符串
            return ""