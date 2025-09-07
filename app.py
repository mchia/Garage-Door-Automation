import os
import cv2
import time
import bcrypt
import sqlite3
import requests
import numpy as np
from time import sleep
from user_agents import parse
from datetime import datetime
from dotenv import load_dotenv
# from picamera2 import Picamera2
from gpiozero import OutputDevice
from typing import Any, Iterator, Optional
from flask import (
    Flask,
    session,
    jsonify,
    request,
    redirect,
    Response,
    render_template
)

class GarageAutomation:
    def __init__(self) -> None:
        self.app: Flask = Flask(__name__)
        self.user: Optional[str] = None
        load_dotenv()
        # self.picam2: Optional[Picamera2] = None
        self.relay: Optional[OutputDevice] = None
        self.db: str = "db/users.db"

        self.app.secret_key = os.getenv(key='SECRET_KEY')
        self.app.add_url_rule(rule='/', view_func=self.launchPage)
        self.app.add_url_rule(rule="/validateLogin", view_func=self.validateLogin, methods=["POST"])
        self.app.add_url_rule(rule="/dashboard", view_func=self.launchDashboard)

        self.app.add_url_rule(rule='/gpioToggle', view_func=self.gpioToggle, methods=["GET"])
        self.app.add_url_rule(rule='/liveView', view_func=self.launchLiveView)
        self.app.add_url_rule(rule='/logbook', view_func=self.launchLogs)
        # self.app.add_url_rule(rule='/cameraView', view_func=self.cameraView)

    # HTML Views #
    def launchPage(self) -> str:
        """
        Method to render the login page.
        """
        return render_template(template_name_or_list='login.html')
    
    def launchDashboard(self) -> str:
        """
        Method to redirect user to login page if logged_in flag is False.
        Otherwise user will be redirected to the dashboard.
        """
        if not session.get("logged_in"):
            return redirect("/")

        return render_template(template_name_or_list='dashboard.html', user=self.user)

    def launchLiveView(self) -> str:
        if not session.get("logged_in"):
            return redirect("/")

        return render_template(template_name_or_list='liveView.html')

    def launchLogs(self) -> str:
        if not session.get("logged_in"):
            return redirect("/")

        rows: list[Any] = self.retrieve_logs()
        return render_template(template_name_or_list='logs.html', rows=rows)

    # Picamera2 Controls #
    # def start_camera(self) -> None:
    #     if self.picam2 is None:
    #         self.picam2: Picamera2 = Picamera2()
    #         self.picam2.awb_mode = 'fluorescent'
    #         self.picam2.start()

    # def stop_camera(self) -> None:
    #     if self.picam2 is not None:
    #         self.picam2.close()
    #         self.picam2: Optional[Picamera2] = None

    # def cameraView(self) -> Response:
    #     """
    #     Produces a live view of camera by calling generate_frames() to continuously return bytes.

    #     Returns:
    #         Response containing jpeg bytes and mimetype (Type of content contained in HTTP response)
    #         'multipart/x-mixed-replace' sends multiple parts of the stream in the same connection and replaces the previous one.
    #         'boundary=frame' is a delimiter, in this case the delimiter is frames.
    #     """

    #     self.start_camera()

    #     def generate_frames() -> Iterator[bytes]:
    #         """
    #         Function to access piCamera module on Raspberry PI :
    #             1) Capture a single frame as a NumPy array.
    #             2) Encode the captured NumPy array as JPEG (Skip if encoding fails).
    #             3) Converts encoded JPEG frames into bytes.
    #             4) Yields each captured frame and sends back to camera to display live feed.

    #         Yields to retain function state unlike 'return' which has to restart.
    #         Yield continues from previous yield until stoppped -> More memory efficient.
    #         """
    #         while True:
    #             frame: np.ndarray = self.picam2.capture_array()
    #             ret, jpeg = cv2.imencode('.jpg', frame)
    #             if not ret:
    #                 continue
    #             frame_bytes: bytes = jpeg.tobytes()
    #             yield (b'--frame\r\n'
    #                 b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    #     return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

    # Pin Controls #
    def get_relay(self) -> OutputDevice:
        self.relay = OutputDevice(pin=17, active_high=True, initial_value=False)

        return self.relay

    def gpioToggle(self):
        try:
            relay: OutputDevice = self.get_relay()
            relay.on()
            sleep(0.5)
            relay.off()
            relay.close()
        except Exception as e:
            print(e)
        finally:
            self.relay: OutputDevice = None

        return Response(status=200)

    # DB Calls #
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
        conn: sqlite3.Connection = sqlite3.connect(self.db, isolation_level=None)
        cursor: sqlite3.Cursor = conn.cursor()

        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        result: Any = cursor.fetchone()

        if result is None:
            return jsonify({"status": "fail", "message": "Invalid credentials"}), 400

        stored_hash: bytes = result[0].encode('utf-8')

        is_valid: bool = bcrypt.checkpw(password=pwd_attempted, hashed_password=stored_hash)
        if is_valid:
            cursor.executescript(open("db/login.sql").read())
            cursor.executescript(open("db/ip_logs.sql").read())
            self.user: str = username
            session["logged_in"] = True
            self.store_login_data(cursor=cursor)
            conn.close()
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "fail", "message": "Invalid credentials"}), 400

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
        user_data: dict[str, str | float | None] = self.user_info()
        ip_data: dict[str, str | float | None] = self.ip_find()
        loginTime: list[str] = datetime.now().isoformat(sep=" ").split(" ")

        # Store login details
        cursor.execute(
            """
            INSERT INTO logbook (
                user_id,
                ip_address,
                login_date,
                login_time,
                browser,
                browser_version,
                os,
                os_version,
                device
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
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
        conn: sqlite3.Connection = sqlite3.connect(self.db)
        conn.row_factory = sqlite3.Row
        cursor: sqlite3.Cursor = conn.cursor()

        with open("db/logs.sql") as f:
            sql: str = f.read()
        cursor.execute(sql)
        rows: list[Any] = cursor.fetchall()

        conn.close()
        return rows

    # IP & User Metadata #
    def ip_find(self) -> dict[str, str | float | None]:
        """
        Method to record metedata related to IP addresses when a user logs in.

        Returns:
            A dictionary of relevant metadata.
        """
        ip: Optional[str] = request.headers.get("CF-Connecting-IP")
        if not ip:
            xff: Optional[str] = request.headers.get("X-Forwarded-For")
            if xff:
                ip: str = xff.split(",")[0].strip()
            else:
                ip: Optional[str] = request.remote_addr

        # If IP is private, make a GET request to "https://api.ipify.org" to return the public address.
        if ip.startswith("127.") or ip.startswith("192.168.") or ip.startswith("10."):
            try:
                public_ip: str = requests.get("https://api.ipify.org").text
            except:
                public_ip: str = ip

        try:
            ip_metadata: Response = requests.get(f"http://ipinfo.io/{public_ip}/json")
            if ip_metadata.status_code == 200:
                data: Optional[Any] = ip_metadata.json()
                ip_data: dict[str, str | float] = {
                    "ip_address": public_ip,
                    "city": data.get("city"),
                    "region": data.get("region"),
                    "country": data.get("country"),
                    "latitude": float(data.get("loc").split(",")[0]),
                    "longitude": float(data.get("loc").split(",")[1])
                }
                return ip_data
        except:
            ip_data: dict[str, str | None] = {
                "ip": public_ip,
                "city": None,
                "region": None,
                "country": None,
                "latitude": None,
                "longitude": None
            }
            return ip_data

    def user_info(self) -> dict[Optional[str]]:
        """
        Method to return metadata about the device used to access the app.
        
        Returns:
            A dictionary of relevant metadata.
        
        """
        user_agent: Any = parse(user_agent_string=request.headers.get("User-Agent"))
        browser: Any = user_agent.browser.family
        browser_version: Any = user_agent.browser.version_string
        operating_system: Any = user_agent.os.family
        os_version: Any = user_agent.os.version_string
        device: Any = user_agent.device.family

        return {
            "browser": browser,
            "browser_version": browser_version,
            "os": operating_system,
            "os_version": os_version,
            "device": device
        }

    # Run
    def run(self) -> None: 
        """
        Method that runs the Flask website.
        Utilises host 0.0.0.0 to allow external access.
        """
        self.app.run()

def create_app() -> Flask:
    garage: GarageAutomation = GarageAutomation()
    return garage.app

app: Flask = create_app()

if __name__ == "__main__":
    app.run(debug=False, use_reloader=False, host="0.0.0.0", port=8000)