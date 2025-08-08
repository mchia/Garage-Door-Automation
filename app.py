import os
import bcrypt
import sqlite3
from typing import Any
from dotenv import load_dotenv
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
        self.user: str = None
        load_dotenv()
        self.app.secret_key = os.getenv(key='SECRET_KEY')
        self.app.add_url_rule(rule='/', view_func=self.launchPage)
        self.app.add_url_rule(rule="/validateLogin", view_func=self.validateLogin, methods=["POST"])
        self.app.add_url_rule(rule="/launchDashboard", view_func=self.launchDashboard)

        self.app.add_url_rule(rule='/openDoor', view_func=self.openDoor, methods=["GET"])
        self.app.add_url_rule(rule='/closeDoor', view_func=self.closeDoor, methods=["GET"])
        self.app.add_url_rule(rule='/pauseDoor', view_func=self.pauseDoor, methods=["GET"])
        self.app.add_url_rule(rule='/resumeDoor', view_func=self.resumeDoor, methods=["GET"])
        self.app.add_url_rule(rule='/cameraView', view_func=self.cameraView, methods=["GET"])

    def launchPage(self) -> str:
        """
        Method to render the login page.
        """
        return render_template(template_name_or_list='login.html')
    
    def launchDashboard(self) -> str:
        """
        Method to redirect user to login page if logged_in flag is False.
        Otherwisem user will be redirected to the dashboard.
        """
        if not session.get("logged_in"):
            return redirect("/")

        return render_template(template_name_or_list='dashboard.html', user=self.user)

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
        conn: sqlite3.Connection = sqlite3.connect("db/users.db")
        cursor: sqlite3.Cursor = conn.cursor()

        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        result: Any = cursor.fetchone()
        conn.close()

        if result is None:
            return jsonify({"status": "fail", "message": "Invalid credentials"}), 400

        stored_hash: bytes = result[0].encode('utf-8')

        is_valid: bool = bcrypt.checkpw(password=pwd_attempted, hashed_password=stored_hash)
        if is_valid:
            self.user: str= username
            session["logged_in"] = True
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "fail", "message": "Invalid credentials"}), 400

    def openDoor(self) -> Response:
        print("Door Opening")
        return Response(status=200)

    def closeDoor(self) -> Response:
        print("Door Closing")
        return Response(status=200)

    def pauseDoor(self) -> Response:
        print("Door Paused")
        return Response(status=200)

    def resumeDoor(self) -> Response:
        print("Door Resuming")
        return Response(status=200)

    def cameraView(self) -> Response:
        print("Camera View")
        return Response(status=200)

    def run(self) -> None: 
        self.app.run(debug=True)

if __name__ == "__main__":
    garage_app: GarageAutomation = GarageAutomation()
    app: Flask = garage_app.app