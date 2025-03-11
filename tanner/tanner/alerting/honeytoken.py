import datetime
import logging
import requests
import geoip2
import base64
from geoip2.database import Reader
import json

from tanner.config import TannerConfig
from azure.communication.email import EmailClient

class HoneyToken:
    """
    A class to trigger a honeytoken alert. When triggered, it sends an email 
    alert containing the visitor's IP, geo location, and request details.
    """

    def __init__(self, 
                 session):
        """
        Initialize the HoneyToken instance with SMTP settings and email addresses.
        """
        self.session = session
        self.from_addr = TannerConfig.get("HONEYTOKEN", "mail_sender")
        self.to_addr = TannerConfig.get("HONEYTOKEN", "mail_recipient")
        self.connection_string = TannerConfig.get("HONEYTOKEN", "connection_string")
        self.logger = logging.getLogger(__name__)


    async def trigger_token_alert(self):
        """
        Trigger the alert by gathering client details, performing a geo IP lookup,
        and sending an alert email asynchronously.
        """

        ip = self.session.ip
        user_agent = self.session.user_agent
        path = self.session.paths[0]['path'] 
        info, geo_map_url = self.find_location(ip)
        tor_exit_node = self.is_tor_exit_node(ip)
        if geo_map_url:
            map_image_base64 = self.get_base64_encoded_image(geo_map_url)
        else:
            map_image_base64 = None
        now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        subject = "Honeytoken was Triggered"
        message_body = (
            f"<html>"
            f"<body>"
            f"<h3>A Honeytoken was Triggered</h3>"
            f"<p><strong>Honeytoken Path:</strong> {path}</p>"
            f"<p><strong>Date and Time:</strong> {now} UTC</p>"
            f"<p><strong>IP Address:</strong> {ip}</p>"
            f"<p><strong>User Agent:</strong> {user_agent}</p>"
            f"<p><strong>Known Tor Exit Node:</strong> {'Yes' if tor_exit_node else 'No'}</p>"
            f"<p><strong>Location:</strong><br> Country: {info.get('country')}<br>"
            f"Region: {info.get('region')}<br> City: {info.get('city')}<br> Zip Code: {info.get('zip_code')}</p>"
            f"<p><strong>Geo Info:</strong> {info.get('latitude')},{info.get('longitude')}</p>"
            f"<img src='data:image/png;base64,{map_image_base64}' alt='Map with location'></img>"
            f"</body>"
            f"</html>"
        )

        # Create the email message
        message = {
            "content": {
                "subject": subject,
                "html": message_body,
            },
            "recipients": {
                "to": [
                    {
                        "address": f"<{self.to_addr}>",
                    }
                ]
            },
            "senderAddress": f"<{self.from_addr}>",
        }
        self.logger.info(f"Sending honeytoken alert email: {json.dumps(message, indent=2)}")

        # Send the email using Azure Communication Services EmailClient
        email_client = EmailClient.from_connection_string(self.connection_string)
        poller = email_client.begin_send(message)
        result = poller.result()

        self.logger.info(f"Honeytoken alert email sent with status: {result}")

    def is_tor_exit_node(self, ip):
        """
        Check if the given IP address is a known Tor exit node.
        """
        try:
            response = requests.get(f"https://check.torproject.org/exit-addresses")
            if response.status_code == 200:
                exit_nodes = response.text
                return ip in exit_nodes
            else:
                return False
        except requests.RequestException as e:
            self.logger.info(f"Error checking Tor exit nodes: {e}")
            return False
        
    @staticmethod
    def find_location(ip):
        reader = Reader(TannerConfig.get("DATA", "geo_db"))
        try:
            location = reader.city(ip)
            info = dict(
                country=location.country.name,
                country_code=location.country.iso_code,
                city=location.city.name,
                region=location.subdivisions.most_specific.name,
                zip_code=location.postal.code,
                latitude=location.location.latitude,
                longitude=location.location.longitude
            )

            # get static map picture
            geo_map = f"https://atlas.microsoft.com/map/static/png?api-version=1.0&center={info['longitude']},{info['latitude']}&zoom=6&width=600&height=400&subscription-key={TannerConfig.get('HONEYTOKEN','maps_subscription_key')}&pins=default||{info['longitude']} {info['latitude']}&tilesetId=microsoft.base.road&language=en-US"
        except geoip2.errors.AddressNotFoundError:
            info = {
                "country": "Unknown",
                "country_code": "Unknown",
                "city": "Unknown",
                "region": "Unknown",
                "zip_code": "Unknown",
                "latitude": "Unknown",
                "longitude": "Unknown"
            }
            geo_map = None
        return info, geo_map

    @staticmethod
    def get_base64_encoded_image(url):
        response = requests.get(url)
        if response.status_code == 200:
            return base64.b64encode(response.content).decode('utf-8')
        return None