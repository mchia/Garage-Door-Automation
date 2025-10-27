
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

    @contextmanager
    def get_camera(self) -> Iterator[Picamera2]:
        """
        Context manager for the PiCamera2.
        Ensures the camera is properly closed after use.
        """
        camera: Picamera2 = Picamera2()
        try:
            yield camera
        finally:
            camera.close()

    def cameraView(self) -> Response:
        """
        Produces a live MJPEG stream from the camera.
        """

        def generate_frames() -> Iterator[bytes]:
            """
            Generator function to capture frames continuously and yield
            them as JPEG byte streams.
            """
            with self.get_camera() as camera:
                self.hw_logger(hardware='Garage Camera')
                while True:
                    try:
                        frame: np.ndarray = camera.capture_array()
                        ret, jpeg = cv2.imencode('.jpg', frame)
                        if not ret:
                            continue
                        frame_bytes: bytes = jpeg.tobytes()
                        yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n'
                    except Exception as e:
                        print("Camera frame capture error:", e)
                        break

        return Response(
            generate_frames(),
            mimetype='multipart/x-mixed-replace; boundary=frame',
            direct_passthrough=True
        )