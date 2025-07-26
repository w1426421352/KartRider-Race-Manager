# 文件名: core/db_manager.py (V2.0 - 增加地图池管理和扩展类型)

import sqlite3
import json
import os

class DBManager:
    _instance = None
    def __new__(cls, db_path='data/competition.db'):
        if cls._instance is None:
            cls._instance = super(DBManager, cls).__new__(cls)
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            cls._instance.conn = sqlite3.connect(db_path, check_same_thread=False)
            cls._instance.conn.row_factory = sqlite3.Row
            cls._instance.cursor = cls._instance.conn.cursor()
            cls._instance._create_tables()
        return cls._instance

    def _create_tables(self):
        sql_script = """
            CREATE TABLE IF NOT EXISTS accounts ( id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, hashed_password TEXT, salt TEXT, ingame_id TEXT, display_name TEXT );
            CREATE TABLE IF NOT EXISTS maps ( id TEXT PRIMARY KEY, theme TEXT, name_cn TEXT, name_tw TEXT, name_kr TEXT, name_en TEXT, difficulty INTEGER, game_type TEXT, has_reverse_mode BOOLEAN NOT NULL DEFAULT 0, tags TEXT );
            CREATE TABLE IF NOT EXISTS rulesets ( id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, author TEXT, ruleset_json TEXT NOT NULL );
            CREATE TABLE IF NOT EXISTS match_history ( id INTEGER PRIMARY KEY AUTOINCREMENT, match_name TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, ruleset_id INTEGER, result_json TEXT, FOREIGN KEY (ruleset_id) REFERENCES rulesets (id) );
            
            -- 新增: 地图池表
            CREATE TABLE IF NOT EXISTS map_pools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                selected_maps TEXT -- 存储地图ID的JSON列表, e.g., ["village_R01", "forest_I01_rvs"]
            );
        """
        self.cursor.executescript(sql_script)
        self.conn.commit()
    
    # --- 新增/修改的地图池管理方法 ---
    def get_all_map_pools(self):
        """获取所有地图池的名称和ID"""
        self.cursor.execute("SELECT id, name FROM map_pools ORDER BY name")
        return self.cursor.fetchall()

    def get_map_pool_by_name(self, name):
        """根据名称获取一个地图池"""
        self.cursor.execute("SELECT * FROM map_pools WHERE name = ?", (name,))
        row = self.cursor.fetchone()
        if row:
            return {"id": row["id"], "name": row["name"], "selected_maps": json.loads(row["selected_maps"])}
        return None
        
    def save_map_pool(self, name, selected_maps_list):
        """保存或更新一个地图池"""
        maps_json = json.dumps(selected_maps_list)
        self.cursor.execute(
            "INSERT OR REPLACE INTO map_pools (id, name, selected_maps) VALUES ((SELECT id FROM map_pools WHERE name = ?), ?, ?)",
            (name, name, maps_json)
        )
        self.conn.commit()

    def delete_map_pool(self, name):
        """删除一个地图池"""
        self.cursor.execute("DELETE FROM map_pools WHERE name = ?", (name,))
        self.conn.commit()
        return self.cursor.rowcount > 0

    def save_maps_batch(self, map_data_list):
        # --- 核心修改: gameType现在直接从map_data_list获取，不再自行解析 ---
        sql = """
            INSERT OR REPLACE INTO maps (id, theme, name_cn, name_tw, name_kr, name_en, difficulty, game_type, has_reverse_mode, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        batch_data = []
        for map_data in map_data_list:
            translations = map_data.get('translations', {})
            parts = map_data['id'].split('_')
            theme = parts[0] if parts else "unknown"

            batch_data.append((
                map_data['id'],
                theme,
                translations.get('cn'),
                translations.get('tw'),
                translations.get('kr'),
                translations.get('en'),
                map_data.get('difficulty'),
                map_data.get('game_type', '其他'), # 直接使用来自MapManager的、更准确的类型
                map_data.get('has_reverse_mode', False),
                json.dumps(map_data.get('tags', []))
            ))
        self.cursor.executemany(sql, batch_data)
        self.conn.commit()

    # ... 其余所有方法保持不变 ...
    def create_account(self, username, hashed_password, salt, ingame_id=None, display_name=None):
        try:
            db_username = username if username else None; self.cursor.execute( "INSERT INTO accounts (username, hashed_password, salt, ingame_id, display_name) VALUES (?, ?, ?, ?, ?)", (db_username, hashed_password, salt, ingame_id, display_name) ); self.conn.commit(); return self.cursor.lastrowid
        except sqlite3.IntegrityError: return None
    def get_account_by_username(self, username):
        self.cursor.execute("SELECT * FROM accounts WHERE username = ?", (username,)); return self.cursor.fetchone()
    def get_account_by_id(self, user_id):
        self.cursor.execute("SELECT * FROM accounts WHERE id = ?", (user_id,)); return self.cursor.fetchone()
    def get_all_accounts(self):
        self.cursor.execute("SELECT id, username, ingame_id, display_name FROM accounts ORDER BY username"); return self.cursor.fetchall()
    def update_account(self, user_id, username, ingame_id, display_name):
        try:
            db_username = username if username else None; self.cursor.execute( "UPDATE accounts SET username = ?, ingame_id = ?, display_name = ? WHERE id = ?", (db_username, ingame_id, display_name, user_id) ); self.conn.commit(); return True
        except sqlite3.IntegrityError: return False
    def update_password(self, user_id, hashed_password, salt):
        self.cursor.execute( "UPDATE accounts SET hashed_password = ?, salt = ? WHERE id = ?", (hashed_password, salt, user_id) ); self.conn.commit(); return True
    def delete_account(self, user_id):
        self.cursor.execute("DELETE FROM accounts WHERE id = ?", (user_id,)); self.conn.commit(); return self.cursor.rowcount > 0
    def clear_maps_table(self):
        self.cursor.execute("DELETE FROM maps"); self.conn.commit()
    def get_all_maps_structured_by_theme(self):
        self.cursor.execute("SELECT * FROM maps ORDER BY theme, id"); all_maps = self.cursor.fetchall()
        structured_maps = {}
        for map_data in all_maps:
            theme = map_data['theme'] or "未知主题"
            if theme not in structured_maps: structured_maps[theme] = []
            structured_maps[theme].append(dict(map_data))
        return structured_maps
    def update_map_details(self, map_id, field_name, new_value):
        allowed_fields = ['name_cn', 'name_tw', 'name_kr', 'name_en', 'difficulty', 'tags']
        if field_name not in allowed_fields: return False
        sql = f"UPDATE maps SET {field_name} = ? WHERE id = ?"; self.cursor.execute(sql, (new_value, map_id)); self.conn.commit()
        return self.cursor.rowcount > 0
    def close(self):
        if self.conn: self.conn.close()