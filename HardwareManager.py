
from time import sleep
import cv2, numpy as np
from flask import Response
from picamera2 import Picamera2
from gpiozero import OutputDevice
from contextlib import contextmanager
from typing import Iterator, Optional, Callable

class HardwareManager:
    def __init__(self, relay_pin: int = 17, hw_logger: Callable[[str, str], None] = None) -> None:
        self.relay_pin: int = relay_pin
        self.picam2: Optional[Picamera2] = None
        self.hw_logger = hw_logger

    @contextmanager
    def get_relay(self):
        """
        Initialize and return the relay GPIO output device.

        Returns:
            OutputDevice: The initialized relay object.
        """
        relay: OutputDevice = OutputDevice(pin=self.relay_pin, active_high=True, initial_value=False)

        try:
            yield relay
        finally:
            relay.close()

    def gpioToggle(self) -> Response:
        """
        Method to trigger the relay module on/off.
        Simulates physically pressing the on/off buttons.

        Returns:
            Response codes:
                200 : No issues.
                400 : Issue
        """
        try:
            with self.get_relay() as relay:
                relay.on()
                sleep(0.5)
                relay.off()
            self.hw_logger(hardware='Garage Door')
        except Exception:
            return Response(status=400)
        else:
            return Response(status=200)

    def start_camera(self) -> None:
        if self.picam2 is None:
            self.picam2: Picamera2 = Picamera2()
            self.picam2.awb_mode = 'fluorescent'
            self.picam2.start()

    def cameraView(self) -> Response:
        """
        Produces a live view of camera by calling generate_frames() to continuously return bytes.

        Returns:
            Response containing jpeg bytes and mimetype (Type of content contained in HTTP response)
            'multipart/x-mixed-replace' sends multiple parts of the stream in the same connection and replaces the previous one.
            'boundary=frame' is a delimiter, in this case the delimiter is frames.
        """

        self.start_camera()

        def generate_frames() -> Iterator[bytes]:
            """
            Function to access piCamera module on Raspberry PI :
                1) Capture a single frame as a NumPy array.
                2) Encode the captured NumPy array as JPEG (Skip if encoding fails).
                3) Converts encoded JPEG frames into bytes.
                4) Yields each captured frame and sends back to camera to display live feed.

            Yields to retain function state unlike 'return' which has to restart.
            Yield continues from previous yield until stoppped -> More memory efficient.
            """
            while True:
                frame: np.ndarray = self.picam2.capture_array()
                ret, jpeg = cv2.imencode('.jpg', frame)
                if not ret:
                    continue
                frame_bytes: bytes = jpeg.tobytes()
                yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

        return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')