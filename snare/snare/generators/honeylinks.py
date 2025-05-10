import os
import datetime
import time
import logging
import requests

from snare.config import SnareConfig

class HoneylinksGenerator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        if os.getenv("IS_LOCAL") == "true":
            self.webhook_url = SnareConfig.get("FEATURES", "WEBHOOK-URL-LOCAL")
        else:
            self.webhook_url = SnareConfig.get("FEATURES", "WEBHOOK-URL-DEPLOYMENT")

    def trigger_honeylink_alert(self, data):
        """
        Trigger an alert by sending a request to the webhook endpoint.
        """
        ip = data["peer"]["ip"]
        path = data["path"]
        now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        # Construct the payload
        payload = {
            "channel": "HTTP",
            "token_type": "honeylink",
            "src_ip": ip,
            "time": now,
            "memo": f"{path} - Triggered",
            "additional_info": self._find_location(ip),
            "known_tor_exit_node": self._is_tor_exit_node(ip)
        }

        # Send the request to the webhook
        try:
            response = requests.post(self.webhook_url, json=payload)
            if response.status_code != 200:
                self.logger.error(f"Failed to send honeylink alert. Status code: {response.status_code}, Response: {response.text}")
        except requests.RequestException as e:
            self.logger.error(f"Error sending honeylink alert to webhook: {e}")

    def _find_location(self, ip):
        """
        Find the geographic location of an IP address.
        """
        url = f"http://ip-api.com/json/{ip}?fields=status,countryCode,continent,regionName,timezone,city,zip,lat,lon,org,as,mobile,proxy"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                info = response.json()
                if info.get('status') == 'success':
                    return {
                        "loc": f"{info.get('lat')},{info.get('lon')}",
                        "org": info.get('org'),
                        "city": info.get('city'),
                        "country": info.get('countryCode'),
                        "region": info.get('regionName'),
                        "timezone": info.get('timezone'),
                        "postal": info.get('zip'),
                        "as": info.get('as'),
                        "continent": info.get('continent'),
                        "mobile": info.get('mobile'),
                        "proxy": info.get('proxy')
                    }
            else:
                self.logger.error(f"Error retrieving location for IP {ip}: {response.status_code}")
        except requests.RequestException as e:
            self.logger.error(f"Error retrieving location for IP {ip}: {e}")
        return {}
    
    def _is_tor_exit_node(self, ip):
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
        
