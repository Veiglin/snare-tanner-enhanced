import logging
import aiohttp
import aiohttp_jinja2
import jinja2
import ssl
import os
import random

from aiohttp import web
from aiohttp.web import StaticResource as StaticRoute

from snare.middlewares import SnareMiddleware
from snare.tanner_handler import TannerHandler
from snare.config import SnareConfig
from snare.generators.honeylinks import HoneylinksGenerator
from snare.utils.snare_helpers import print_color

class HttpRequestHandler:
    def __init__(self, meta, run_args, snare_uuid, debug=False, keep_alive=75, **kwargs):
        self.run_args = run_args
        self.dir = run_args.full_page_path
        self.meta = meta
        self.snare_uuid = snare_uuid
        self.logger = logging.getLogger(__name__)
        self.sroute = StaticRoute(name=None, prefix="/", directory=self.dir)
        self.tanner_handler = TannerHandler(run_args, meta, snare_uuid)
        if SnareConfig.get("FEATURES", "enabled") is True:
            self.dynamic_routes = self.generate_dynamic_route_map("/opt/snare/honeytokens/common.txt")
            self.track_dir = os.path.join("/opt/snare", "honeytokens")
            self.track_path = os.path.join(self.track_dir, "Honeytokens.txt")
            self.honeylink_paths = self.get_honeylink_paths()
            self.hl = HoneylinksGenerator()

    def generate_dynamic_route_map(self, wordlist_path):
        try:
            with open(wordlist_path, "r") as f:
                words = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        except Exception as e:
            self.logger.error(f"Failed to load wordlist: {e}")
            return {}

        random.shuffle(words)
        sampled = words[:100]  # Limit to avoid overload

        route_map = {}
        for path in sampled:
            full_path = "/" + path.lstrip("/")
            choice = random.choices(
                ["401", "403", "500"],
                weights=[0.4, 0.4, 0.2],
                k=1
            )[0]
            route_map[full_path] = (f"/status_{choice}", int(choice))
        
        for path, (status_path, status_code) in route_map.items():
            self.logger.debug(f"Adding Route {path} → {status_code} ({status_path})")

        return route_map
    
    def get_honeylink_paths(self):
        """
        Get the honeylink paths from Honeytokens.txt and static paths in config.
        """
        # load Honeytokens.txt
        if not os.path.exists(self.track_path):
            print_color("Honeytokens.txt not found. Can not get honeylink paths", "WARNING")
            return 
        with open(self.track_path, "r") as f:
            honeytokens = f.read().splitlines()
        
        # filter out honeylink paths
        honeylink_paths = []
        for path in honeytokens:
            if not (path.lower()).endswith(".xlsx") and not (path.lower()).endswith(".pdf") and not (path.lower()).endswith(".docx"):
                # there is not an / in the start of the path, add it
                if not path.startswith("/"):
                    path = "/" + path
                honeylink_paths.append(path)

        # add honeylink paths from config if any
        static_paths = SnareConfig.get("HONEYLINK", "STATIC-PATHS")
        if static_paths:
            for path in static_paths:
                path = path.strip()
                if not path.startswith("/"):
                    path = "/" + path
                honeylink_paths.append(path)
        print_color(f"Adding the honeylink paths: {honeylink_paths}", "INFO")
        return honeylink_paths

    async def submit_slurp(self, data):
        try:
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
                r = await session.post(
                    "https://{0}:8080/api?auth={1}&chan=snare_test&msg={2}".format(
                        self.run_args.slurp_host, self.run_args.slurp_auth, data
                    ),
                    json=data,
                    timeout=10.0,
                )
                assert r.status == 200
                r.close()
        except Exception as e:
            self.logger.error("Error submitting slurp: %s", e)

    async def handle_request(self, request):
        self.logger.info("Request path: {0}".format(request.path_qs))
        path = request.path

        data = self.tanner_handler.create_data(request, 200)
        if (SnareConfig.get("FEATURES", "enabled") is True):
            if (self.honeylink_paths) and (path in self.honeylink_paths):
                self.logger.info(f"Honeylink path triggered: {path}")
                self.hl.trigger_honeylink_alert(data=data)

        # Submit the event to the TANNER service
        event_result = await self.tanner_handler.submit_data(data)

        # Log the event to slurp service if enabled
        if self.run_args.slurp_enabled:
            await self.submit_slurp(request.path_qs)

        content, headers, status_code = await self.tanner_handler.parse_tanner_response(
            request.path_qs, event_result["response"]["message"]["detection"]
        )

        if self.run_args.server_header:
            headers["Server"] = self.run_args.server_header

        if "cookies" in data and "sess_uuid" in data["cookies"]:
            previous_sess_uuid = data["cookies"]["sess_uuid"]
        else:
            previous_sess_uuid = None

        if event_result is not None and "sess_uuid" in event_result["response"]["message"]:
            cur_sess_id = event_result["response"]["message"]["sess_uuid"]
            if previous_sess_uuid is None or not previous_sess_uuid.strip() or previous_sess_uuid != cur_sess_id:
                headers.add("Set-Cookie", "sess_uuid=" + cur_sess_id)

        if SnareConfig.get("FEATURES", "enabled") is True:
            # Dynamic route error handling
            if path in self.dynamic_routes:
                status_path, status_code = self.dynamic_routes[path]
                self.logger.info(f"Dynamic route trap triggered: {path} → {status_code}")
                directed_error_page = "/"+str(status_code)
                if (self.honeylink_paths) and (directed_error_page in self.honeylink_paths):
                    self.logger.info(f"Honeylink path triggered: {directed_error_page}")
                    self.hl.trigger_honeylink_alert(data=data)
                return await self.serve_error_page(status_path, status_code)
    
            if path == "/400":
                return await self.serve_error_page("/status_400", 400)
            if path == "/401":
                return await self.serve_error_page("/status_401", 401)
            if path == "/403":
                return await self.serve_error_page("/status_403", 403)
            if path == "/500":
                return await self.serve_error_page("/status_500", 500)
            
        return web.Response(body=content, status=status_code, headers=headers)

    async def start(self):
        app = web.Application()
        app.add_routes([web.route("*", "/{tail:.*}", self.handle_request)])
        aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(self.dir))
        middleware = SnareMiddleware(
            error_400=self.meta["/status_400"].get("hash", None),
            error_401=self.meta["/status_401"].get("hash", None),
            error_403=self.meta["/status_403"].get("hash", None),
            error_404=self.meta["/status_404"].get("hash"),
            error_500=self.meta["/status_500"].get("hash", None),
            headers=self.meta["/status_404"].get("headers", []),
            server_header=self.run_args.server_header,
        )
        middleware.setup_middlewares(app)

        self.runner = web.AppRunner(app)
        await self.runner.setup()

        is_local = os.getenv("IS_LOCAL", "false").lower() == "true"

        if not is_local:
            base_domain = SnareConfig.get("DOMAIN", "BASE_DOMAIN")
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_context.load_cert_chain(
                certfile=f'/etc/letsencrypt/live/{base_domain}/fullchain.pem',
                keyfile=f'/etc/letsencrypt/live/{base_domain}/privkey.pem'
            )
            site = web.TCPSite(self.runner, self.run_args.host_ip, self.run_args.port, ssl_context=ssl_context)
        else:
            site = web.TCPSite(self.runner, self.run_args.host_ip, self.run_args.port)

        await site.start()
        names = sorted(str(s.name) for s in self.runner.sites)
        print("======== Running on {} ========\n" "(Press CTRL+C to quit)".format(", ".join(names)))

    async def stop(self):
        await self.runner.cleanup()

    async def serve_error_page(self, status_path, status_code):
        try:
            file_hash = self.meta[status_path]["hash"]
            file_path = os.path.join(self.dir, file_hash)
            with open(file_path, "rb") as f:
                content = f.read()
        except Exception:
            content = f"Error {status_code}".encode()

        headers = {}
        if self.run_args.server_header:
            headers["Server"] = self.run_args.server_header

        for header in self.meta.get(status_path, {}).get("headers", []):
            for k, v in header.items():
                headers[k] = v

        return web.Response(body=content, status=status_code, headers=headers)
