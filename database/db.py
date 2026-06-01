"""
ماژول دیتابیس SQLite - آپلودر تریاک
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Tuple, Any


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._create_tables()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _create_tables(self):
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    joined_at TEXT DEFAULT (datetime('now', 'localtime')),
                    is_banned INTEGER DEFAULT 0,
                    ban_reason TEXT DEFAULT NULL
                );

                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id TEXT NOT NULL,
                    file_unique_id TEXT NOT NULL,
                    file_name TEXT,
                    file_size INTEGER DEFAULT 0,
                    file_type TEXT,
                    mime_type TEXT,
                    uploaded_by INTEGER NOT NULL,
                    uploaded_at TEXT DEFAULT (datetime('now', 'localtime')),
                    storage_message_id INTEGER DEFAULT 0,
                    download_count INTEGER DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS admins (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    role TEXT DEFAULT 'admin',
                    added_by INTEGER NOT NULL,
                    added_at TEXT DEFAULT (datetime('now', 'localtime'))
                );

                CREATE TABLE IF NOT EXISTS channels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id INTEGER NOT NULL,
                    channel_username TEXT,
                    channel_title TEXT,
                    added_at TEXT DEFAULT (datetime('now', 'localtime'))
                );

                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                -- درج تنظیمات پیش‌فرض
                INSERT OR IGNORE INTO settings (key, value) VALUES ('force_join_enabled', '1');
                INSERT OR IGNORE INTO settings (key, value) VALUES ('storage_channel_id', '');
            """)

    # ==================== USERS ====================

    def add_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None):
        with self._connect() as conn:
            conn.execute(
                """INSERT OR IGNORE INTO users (user_id, username, first_name, last_name)
                   VALUES (?, ?, ?, ?)""",
                (user_id, username, first_name, last_name)
            )
            # آپدیت اطلاعات کاربر در صورت تغییر
            conn.execute(
                """UPDATE users SET username = ?, first_name = ?, last_name = ?
                   WHERE user_id = ? AND (username != ? OR first_name != ? OR last_name != ?)""",
                (username, first_name, last_name, user_id, username, first_name, last_name)
            )

    def get_user(self, user_id: int) -> Optional[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()

    def get_all_users(self) -> List[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute("SELECT * FROM users ORDER BY joined_at DESC").fetchall()

    def count_users(self) -> int:
        with self._connect() as conn:
            return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]

    def ban_user(self, user_id: int, reason: str = None):
        with self._connect() as conn:
            conn.execute("UPDATE users SET is_banned = 1, ban_reason = ? WHERE user_id = ?", (reason, user_id))

    def unban_user(self, user_id: int):
        with self._connect() as conn:
            conn.execute("UPDATE users SET is_banned = 0, ban_reason = NULL WHERE user_id = ?", (user_id,))

    def is_banned(self, user_id: int) -> bool:
        with self._connect() as conn:
            row = conn.execute("SELECT is_banned FROM users WHERE user_id = ?", (user_id,)).fetchone()
            return bool(row and row[0])

    def count_banned_users(self) -> int:
        with self._connect() as conn:
            return conn.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1").fetchone()[0]

    def search_users(self, query: str) -> List[sqlite3.Row]:
        with self._connect() as conn:
            q = f"%{query}%"
            return conn.execute(
                """SELECT * FROM users WHERE
                   CAST(user_id AS TEXT) LIKE ? OR
                   username LIKE ? OR
                   first_name LIKE ? OR
                   last_name LIKE ?""",
                (q, q, q, q)
            ).fetchall()

    # ==================== FILES ====================

    def add_file(self, file_id: str, file_unique_id: str, file_name: str = None,
                 file_size: int = 0, file_type: str = None, mime_type: str = None,
                 uploaded_by: int = 0, storage_message_id: int = 0) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """INSERT INTO files (file_id, file_unique_id, file_name, file_size,
                   file_type, mime_type, uploaded_by, storage_message_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (file_id, file_unique_id, file_name, file_size, file_type, mime_type, uploaded_by, storage_message_id)
            )
            return cursor.lastrowid

    def get_file_by_id(self, file_db_id: int) -> Optional[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute("SELECT * FROM files WHERE id = ?", (file_db_id,)).fetchone()

    def get_file_by_unique_id(self, file_unique_id: str) -> Optional[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute("SELECT * FROM files WHERE file_unique_id = ?", (file_unique_id,)).fetchone()

    def get_all_files(self, offset: int = 0, limit: int = 20) -> List[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM files ORDER BY uploaded_at DESC LIMIT ? OFFSET ?",
                (limit, offset)
            ).fetchall()

    def count_files(self) -> int:
        with self._connect() as conn:
            return conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]

    def delete_file(self, file_db_id: int):
        with self._connect() as conn:
            conn.execute("DELETE FROM files WHERE id = ?", (file_db_id,))

    def search_files(self, query: str) -> List[sqlite3.Row]:
        with self._connect() as conn:
            q = f"%{query}%"
            return conn.execute(
                """SELECT * FROM files WHERE
                   file_name LIKE ? OR
                   CAST(id AS TEXT) LIKE ? OR
                   file_unique_id LIKE ?""",
                (q, q, q)
            ).fetchall()

    def increment_download_count(self, file_unique_id: str):
        with self._connect() as conn:
            conn.execute("UPDATE files SET download_count = download_count + 1 WHERE file_unique_id = ?", (file_unique_id,))

    # ==================== ADMINS ====================

    def add_admin(self, user_id: int, username: str = None, first_name: str = None,
                  role: str = 'admin', added_by: int = 0):
        with self._connect() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO admins (user_id, username, first_name, role, added_by)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, username, first_name, role, added_by)
            )

    def remove_admin(self, user_id: int):
        with self._connect() as conn:
            conn.execute("DELETE FROM admins WHERE user_id = ? AND role != 'owner'", (user_id,))

    def get_admin(self, user_id: int) -> Optional[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute("SELECT * FROM admins WHERE user_id = ?", (user_id,)).fetchone()

    def get_all_admins(self) -> List[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute("SELECT * FROM admins ORDER BY role ASC, added_at ASC").fetchall()

    def count_admins(self) -> int:
        with self._connect() as conn:
            return conn.execute("SELECT COUNT(*) FROM admins").fetchone()[0]

    def is_admin(self, user_id: int) -> bool:
        return self.get_admin(user_id) is not None

    def is_owner(self, user_id: int) -> bool:
        admin = self.get_admin(user_id)
        return admin and admin['role'] == 'owner'

    # ==================== CHANNELS ====================

    def add_channel(self, channel_id: int, channel_username: str = None, channel_title: str = None):
        with self._connect() as conn:
            existing = conn.execute("SELECT * FROM channels WHERE channel_id = ?", (channel_id,)).fetchone()
            if not existing:
                conn.execute(
                    """INSERT INTO channels (channel_id, channel_username, channel_title)
                       VALUES (?, ?, ?)""",
                    (channel_id, channel_username, channel_title)
                )
                return True
            return False

    def remove_channel(self, channel_id: int):
        with self._connect() as conn:
            conn.execute("DELETE FROM channels WHERE channel_id = ?", (channel_id,))

    def get_channel(self, channel_id: int) -> Optional[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute("SELECT * FROM channels WHERE channel_id = ?", (channel_id,)).fetchone()

    def get_all_channels(self) -> List[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute("SELECT * FROM channels ORDER BY added_at ASC").fetchall()

    def count_channels(self) -> int:
        with self._connect() as conn:
            return conn.execute("SELECT COUNT(*) FROM channels").fetchone()[0]

    # ==================== SETTINGS ====================

    def get_setting(self, key: str, default: str = None) -> str:
        with self._connect() as conn:
            row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
            return row[0] if row else default

    def set_setting(self, key: str, value: str):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, value)
            )

    def is_force_join_enabled(self) -> bool:
        return self.get_setting('force_join_enabled', '1') == '1'

    def get_storage_channel_id(self) -> Optional[int]:
        val = self.get_setting('storage_channel_id', '')
        if val and val.strip():
            try:
                return int(val.strip())
            except ValueError:
                return None
        return None

    # ==================== STATS ====================

    def get_stats(self) -> dict:
        return {
            'users': self.count_users(),
            'files': self.count_files(),
            'admins': self.count_admins(),
            'banned': self.count_banned_users(),
            'channels': self.count_channels(),
            'force_join': self.is_force_join_enabled(),
        }

    # ==================== BACKUP ====================

    def get_backup_path(self) -> str:
        return self.db_path


# نمونه سراسری از دیتابیس
from config import DB_PATH

db = Database(DB_PATH)
