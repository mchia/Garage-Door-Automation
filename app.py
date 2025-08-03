import os
from dotenv import load_dotenv
from flask import Flask, render_template, Response


class GarageAutomation:
    def __init__(self) -> None:
        self.app: Flask = Flask(__name__)
        
        load_dotenv()
        self.app.secret_key = os.getenv(key='SECRET_KEY')
        # Web page
        self.app.add_url_rule(rule='/', view_func=self.launchPage)

        # Commands with unique routes and correct 'methods' keyword
        self.app.add_url_rule(rule='/openDoor', view_func=self.openDoor, methods=["GET"])
        self.app.add_url_rule(rule='/closeDoor', view_func=self.closeDoor, methods=["GET"])
        self.app.add_url_rule(rule='/pauseDoor', view_func=self.pauseDoor, methods=["GET"])
        self.app.add_url_rule(rule='/resumeDoor', view_func=self.resumeDoor, methods=["GET"])
        self.app.add_url_rule(rule='/cameraView', view_func=self.cameraView, methods=["GET"])

    def launchPage(self) -> str:
        return render_template('launchPage.html')
    
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
    GarageAutomation().run()