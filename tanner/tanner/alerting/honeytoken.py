import datetime
import logging
import geoip2
from geoip2.database import Reader

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
        self.logger = logging.getLogger("tanner.honeytoken.Honeytoken")


    async def trigger_token_alert(self):
        """
        Trigger the alert by gathering client details, performing a geo IP lookup,
        and sending an alert email asynchronously.
        """

        # Extract client details
        #print(self.session.)
        #print(vars(self.session))
        ip = self.session.ip
        user_agent = self.session.user_agent
        info = self.find_location(ip)

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        subject = "Honeytoken Alert: Potential Intruder"
        message_body = (
            f"<html>"
            f"<body>"
            f"<h1>ALERT - Honeytoken Triggered!</h1>"
            f"<p><strong>Date and Time:</strong> {now}</p>"
            f"<p><strong>IP Address:</strong> {ip}</p>"
            f"<p><strong>Location:</strong> {info.get('country', 'Unknown')}, "
            f"{info.get('city', 'Unknown')}, {info.get('zip_code', 'Unknown')}</p>"
            f"<p><strong>User Agent:</strong> {user_agent}</p>"
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

        # Send the email using Azure Communication Services EmailClient
        email_client = EmailClient.from_connection_string(self.connection_string)
        poller = email_client.begin_send(message)
        result = poller.result()

        self.logger.info(f"Honeytoken alert email sent with status: {result}")

    @staticmethod
    def find_location(ip):
        reader = Reader(TannerConfig.get("DATA", "geo_db"))
        try:
            location = reader.city(ip)
            info = dict(
                country=location.country.name,
                country_code=location.country.iso_code,
                city=location.city.name,
                zip_code=location.postal.code,
            )
        except geoip2.errors.AddressNotFoundError:
            info = {
                "country": "NA",
                "country_code": "NA",
                "city": "NA",
                "zip_code": "NA"
            }
        return info