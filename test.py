from user_agents import parse
from dotenv import load_dotenv
from typing import Any, Optional, Union, Generator
import os, requests, dbManager as dbm, HardwareManager as hwm
from flask import (
    Flask,
    session,
    request,
    redirect,
    Response,
    render_template
)

load_dotenv()
ip = os.getenv(key='LINUX_IP')

def intialiseLinuxCam() -> Response:
    """
    Proxy the MJPG stream from the Linux laptop, only if the user is logged in.
    """
    def generate() -> Generator[bytes, None, None]:
        url: str = f"http://192.168.1.117:8080/?action=stream"
        with requests.get(url, stream=True) as r:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    yield chunk

    return Response(generate(), content_type='multipart/x-mixed-replace; boundary=frame')

p = intialiseLinuxCam()

print(p)
