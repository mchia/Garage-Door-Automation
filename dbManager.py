from datetime import datetime
import sqlite3, bcrypt, secrets
from contextlib import contextmanager
from flask import Response, jsonify, request, session
from typing import Generator, Optional, Any, Callable

class dbManager:
    def __init__(self, ip_dict: Callable[[], dict], user_dict: Callable[[], dict]) -> None:
        self.db: str = "db/users.db"
        self.ip_dict: Callable[[], dict] = ip_dict
        self.user_dict: Callable[[], dict] = user_dict
        self.user: Optional[str] = None
        self.role: Optional[str] = None
        self.session_id: str = secrets.token_hex(nbytes=16)

    @contextmanager
    def db_connect(self) -> Generator[sqlite3.Cursor, None, None]:
        """
        Creates connection to self.db as an isolated method for scalability.
        Usaes @contextmanager decorator to allow this top function as a pythonic context manager.
        This approach avoids having to manully call conn.close() each time.
        isolation_level=None sets autocommit.
        conn.row_factory = sqlite3.Row transforms rows into Python like dictionaries for easier access.
        """
        conn: sqlite3.Connection = sqlite3.connect(database=self.db, isolation_level=None)
        conn.row_factory = sqlite3.Row
        cursor: sqlite3.Cursor = conn.cursor()

        try:
            # yield pauses the code and gives control to context manager when called via with.
            # Once done, return control to this method which always calls conn.close() 
            yield cursor
        finally:
            conn.close()

    def validateLogin(self) -> Response:
        """
        Method to validate login credentials against a sqlite database.
        Password is encoded with bcrypt.

        Returns:
            Response containing login status.
        """
        data: Any = request.get_json()
        username: str = data.get("username")
        password_raw: str = data.get("password")

        if not username or not password_raw:
            return jsonify({"status": "fail", "message": "Missing username or password"}), 400

        pwd_attempted: bytes = password_raw.encode('utf-8')

        # Take control from self.db_connect()
        with self.db_connect() as cursor:
            cursor.execute("SELECT password, role FROM users WHERE username = ?", (username,))
            result: Any = cursor.fetchone()

            if result is None:
                return jsonify({"status": "fail", "message": "Invalid credentials"}), 400

            stored_hash: bytes = result[0].encode('utf-8')

            is_valid: bool = bcrypt.checkpw(password=pwd_attempted, hashed_password=stored_hash)
            if is_valid:
                cursor.executescript(open("db/login.sql").read())
                cursor.executescript(open("db/ip_logs.sql").read())
                self.user: str = username
                self.role: str = result[1]
                session["logged_in"] = True
                self.store_login_data(cursor=cursor)
                return jsonify({"status": "success"}), 200
            else:
                return jsonify({"status": "fail", "message": "Invalid credentials"}), 400
            
            # Return control to self.db_connect()

    def user_metadata(self) -> dict:
        return self.user_dict()
    
    def ip_metadata(self) -> dict:
        return self.ip_dict()

    def store_login_data(self, cursor: sqlite3.Cursor) -> None:
        """
        Method to write login data to database.

        Parameters:
            cursor : sqlite3.Cursor
                Cursor object to perfrom write operations.
        """
        user_id_row: Any = cursor.execute(
            "SELECT id FROM users WHERE username = ?",
            (self.user,)
        ).fetchone()

        user_id: str | None = user_id_row[0] if user_id_row else None
        user_data: dict[str, str | float | None] = self.user_metadata()
        ip_data: dict[str, str | float | None] = self.ip_metadata()
        loginTime: list[str] = datetime.now().isoformat(sep=" ").split(" ")

        # Store login details
        cursor.execute(
            """
            INSERT INTO logbook (
                user_id,
                session_id,
                ip_address,
                login_date,
                login_time,
                browser,
                browser_version,
                os,
                os_version,
                device
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                self.session_id,
                ip_data.get("ip_address"),
                loginTime[0],
                loginTime[1].split(".")[0],
                user_data.get("browser"),
                user_data.get("browser_version"),
                user_data.get("os"),
                user_data.get("os_version"),
                user_data.get("device"),
            ),
        )

        # Store unique IP address details
        cursor.execute("""
            INSERT OR IGNORE INTO ip_logs (
                ip_address,
                city,
                region,
                country,
                latitude,
                longitude
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                ip_data.get("ip_address"),
                ip_data.get("city"),
                ip_data.get("region"),
                ip_data.get("country"),
                ip_data.get("latitude"),
                ip_data.get("longitude"),
            ),
        )

    def retrieve_logs(self) -> list[Any]:
        """
        Method to query DB to display logbook of logins in a HTML table.

        Returns
            rows : list[Any]
                Rows from the database in a python list.
        """
        with self.db_connect() as cursor:
            with open("db/logs.sql") as f:
                sql: str = f.read()
            cursor.execute(sql)
            rows: list[Any] = cursor.fetchall()

        return rows

    def userList(self) -> list[str]:
        """
        Method to query DB and return a list of all current usernames.

        Returns
            list[str]
        """
        with self.db_connect() as cursor:
            cursor.execute("SELECT username FROM users WHERE LOWER(role)<>'admin' ORDER BY username ASC")
            return [row[0] for row in cursor.fetchall()]

    def addUser(self) -> Response:
        """
        Method called when adding new users - hashes and encodes passwords before storing in db.
        """
        data: Any = request.get_json()
        username: str = data.get("username")
        password: str = data.get("password")

        pwd_bytes: Any = password.encode("utf-8")
        salt: bytes = bcrypt.gensalt(rounds=12)
        hashed: bytes = bcrypt.hashpw(pwd_bytes, salt)
        hashed_str: str = hashed.decode("utf-8")

        try:
            with self.db_connect() as cursor:
                cursor.execute(
                    "INSERT INTO users (username, role, password) VALUES (?, 'read', ?)",
                    (username, hashed_str)
                )
                return jsonify({"status": "success"}), 200
        except Exception:
            return jsonify({"status": "fail", "message": Exception}), 400

    def removeUser(self) -> Response:
        """
        Method called when removing users from the database.
        """
        data: Any = request.get_json()
        username: str = data.get("Remove")

        try:
            with self.db_connect() as cursor:
                cursor.execute(
                    "DELETE FROM users WHERE username = ?",
                    (username,)
                )
                return jsonify({"status": "success"}), 200
        except Exception:
            return jsonify({"status": "fail", "message": 'User does not exist'}), 400
