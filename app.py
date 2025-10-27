from user_agents import parse
from dotenv import load_dotenv
from typing import Any, Optional
import os, requests, dbManager as dbm, HardwareManager as hwm
from flask import (
    Flask,
    session,
    request,
    redirect,
    Response,
    render_template
)

class GarageAutomation:
    def __init__(self) -> None:
        self.app: Flask = Flask(__name__)

        # Initialise Database and Hardware Managers
        self.db: dbm.dbManager = dbm.dbManager(ip_dict=self.ip_find, user_dict=self.user_info)
        self.hw: hwm.HardwareManager = hwm.HardwareManager(hw_logger=self.db.hardware_logging)

        load_dotenv()
        self.app.secret_key = os.getenv(key='SECRET_KEY')
        self.app.add_url_rule(rule='/', view_func=self.launchPage)
        self.app.add_url_rule(rule="/validateLogin", view_func=self.db.validateLogin, methods=["POST"])
        self.app.add_url_rule(rule="/addUser", view_func=self.db.addUser, methods=["POST"])
        self.app.add_url_rule(rule="/removeUser", view_func=self.db.removeUser, methods=["POST"])
        self.app.add_url_rule(rule="/dashboard", view_func=self.launchDashboard)

        self.app.add_url_rule(rule='/gpioToggle', view_func=self.hw.gpioToggle, methods=["GET"])
        self.app.add_url_rule(rule='/liveView', view_func=self.launchLiveView)
        self.app.add_url_rule(rule='/logbook', view_func=self.launchLogs)
        self.app.add_url_rule(rule='/cameraView', view_func=self.hw.cameraView)
        self.app.add_url_rule(rule='/admin', view_func=self.launchAdmin)

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

        return render_template(
            template_name_or_list='dashboard.html',
            user=self.db.user if hasattr(self.db, "user") else None,
            role=self.db.role if hasattr(self.db, "role") else None
        )

    def launchLiveView(self) -> str:
        """
        Method to redirect user to live view page if logged_in flag is False.
        Otherwise user will be redirected to the dashboard.
        """
        if not session.get("logged_in"):
            return redirect("/")

        return render_template(template_name_or_list='liveView.html')

    def launchLogs(self) -> str:
        if not session.get("logged_in"):
            return redirect("/")

        rows, hw_cols = self.db.retrieve_logs()
        return render_template(template_name_or_list='logs.html', rows=rows, hw_cols=hw_cols)

    def launchAdmin(self) -> str|Response:
        if self.db.role == 'admin':
            return render_template(
                template_name_or_list='admin.html',
                users=self.db.userList()
            )
        else:
            return redirect("/")

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
                ip: str = requests.get("https://api.ipify.org").text
            except:
                ip: str = ip

        try:
            ip_metadata: Response = requests.get(f"http://ipinfo.io/{ip}/json")
            if ip_metadata.status_code == 200:
                data: Optional[Any] = ip_metadata.json()
                ip_data: dict[str, str | float] = {
                    "ip_address": ip,
                    "city": data.get("city"),
                    "region": data.get("region"),
                    "country": data.get("country"),
                    "latitude": float(data.get("loc").split(",")[0]),
                    "longitude": float(data.get("loc").split(",")[1])
                }
                return ip_data

        except Exception:
            ip_data: dict[str, str | None] = {
                "ip": ip,
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

    def action_info(self) -> dict[Optional[str]]:
        pass

    # Run
    def run(self) -> None: 
        """
        Method that runs the Flask website.
        Utilises host 0.0.0.0 to allow external access.
        """
        self.app.run(host='0.0.0.0', port=5000, debug=False)

def create_app() -> Flask:
    garage: GarageAutomation = GarageAutomation()
    return garage.app

app: Flask = create_app()

if __name__ == "__main__":
    app.run(debug=False, use_reloader=False)