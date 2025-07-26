# 文件名: core/auth_manager.py (V1.3 - 采用安全字符集)

import os
import hashlib
import secrets
import re
from core.db_manager import DBManager


class AuthManager:
    _instance = None
    ITERATIONS = 100000
    HASH_ALGORITHM = 'sha256'

    # --- 核心修改: 采用更安全的标点符号集 ---
    ALLOWED_PUNCTUATION_REGEX = r"!@#$%^()_+\-="
    CREDENTIAL_REGEX = re.compile(rf"^[a-zA-Z0-9{ALLOWED_PUNCTUATION_REGEX}]+$")

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AuthManager, cls).__new__(cls)
            cls._instance.db = DBManager()
            cls._instance.active_sessions = {}
        return cls._instance

    def _is_valid_credential_string(self, s: str) -> bool:
        """检查字符串是否只包含允许的账号密码字符"""
        if not s:
            return False
        return bool(self.CREDENTIAL_REGEX.match(s))

    def _hash_password(self, password, salt):
        """使用PBKDF2算法对密码进行哈希。"""
        pwd_hash = hashlib.pbkdf2_hmac(
            self.HASH_ALGORITHM,
            password.encode('utf-8'),
            salt,
            self.ITERATIONS
        )
        return pwd_hash

    def create_account(self, username, password, ingame_id=None, display_name=None):
        """创建新账号，包含字符集验证和密码哈希逻辑。"""
        if not self._is_valid_credential_string(username):
            print(f"错误: 用户名 '{username}' 包含无效字符。")
            return None
        if not self._is_valid_credential_string(password):
            print(f"错误: 密码包含无效字符。")
            return None

        if self.db.get_account_by_username(username):
            print(f"错误: 用户名 '{username}' 已存在。")
            return None

        salt = os.urandom(16)
        hashed_password = self._hash_password(password, salt)
        return self.db.create_account(
            username=username,
            hashed_password=hashed_password.hex(),
            salt=salt.hex(),
            ingame_id=ingame_id,
            display_name=display_name
        )

    def verify_password(self, username, password):
        """验证用户名和密码是否匹配。"""
        account_data = self.db.get_account_by_username(username)
        if not account_data:
            return False

        stored_salt = bytes.fromhex(account_data['salt'])
        stored_hash = bytes.fromhex(account_data['hashed_password'])

        incoming_hash = self._hash_password(password, stored_salt)

        return secrets.compare_digest(stored_hash, incoming_hash)

    def update_password(self, user_id, new_password):
        """更新指定用户的密码"""
        if not self._is_valid_credential_string(new_password):
            print(f"错误: 新密码包含无效字符。")
            return False

        salt = os.urandom(16)
        hashed_password = self._hash_password(new_password, salt)
        return self.db.update_password(user_id, hashed_password.hex(), salt.hex())

    def generate_session_token(self, username):
        """为登录成功的用户生成一个会话令牌。"""
        token = secrets.token_hex(32)
        self.active_sessions[token] = username
        return token

    def verify_session_token(self, token):
        """验证会话令牌是否有效，并返回对应的用户名。"""
        return self.active_sessions.get(token)

    def invalidate_session_token(self, token):
        """使会话令牌失效 (用户登出)"""
        if token in self.active_sessions:
            del self.active_sessions[token]