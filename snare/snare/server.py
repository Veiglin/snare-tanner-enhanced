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


class HttpRequestHandler:
    def __init__(self, meta, run_args, snare_uuid, debug=False, keep_alive=75, **kwargs):
        self.run_args = run_args
        self.dir = run_args.full_page_path
        self.meta = meta
        self.snare_uuid = snare_uuid
        self.logger = logging.getLogger(__name__)
        self.sroute = StaticRoute(name=None, prefix="/", directory=self.dir)
        self.tanner_handler = TannerHandler(run_args, meta, snare_uuid)
        self.dynamic_routes = self.generate_dynamic_route_map("/opt/snare/honeytokens/common.txt")

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

        # Dynamic route error handling
        if path in self.dynamic_routes:
            status_path, status_code = self.dynamic_routes[path]
            self.logger.info(f"Dynamic route trap triggered: {path} → {status_code}")
            return await self.serve_error_page(status_path, status_code)

        if path == "/400":
            return await self.serve_error_page("/status_400", 400)
        if path == "/401":
            return await self.serve_error_page("/status_401", 401)
        if path == "/403":
            return await self.serve_error_page("/status_403", 403)
        if path == "/500":
            return await self.serve_error_page("/status_500", 500)

        data = self.tanner_handler.create_data(request, 200)
        if request.method == "POST":
            post_data = await request.post()
            self.logger.info("POST data:")
            for key, val in post_data.items():
                self.logger.info("\t- {0}: {1}".format(key, val))
            data["post_data"] = dict(post_data)

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

        return web.Response(body=content, status=status_code, headers=headers)

    async def start(self):
        app = web.Application()
        app.add_routes([web.route("*", "/{tail:.*}", self.handle_request)])
        aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(self.dir))
        middleware = SnareMiddleware(
            error_400=self.meta["/status_400"].get("hash"),
            error_401=self.meta["/status_401"].get("hash"),
            error_403=self.meta["/status_403"].get("hash"),
            error_404=self.meta["/status_404"].get("hash"),
            error_500=self.meta["/status_500"].get("hash"),
            headers=self.meta["/status_404"].get("headers", []),
            server_header=self.run_args.server_header,
        )
        middleware.setup_middlewares(app)

        self.runner = web.AppRunner(app)
        await self.runner.setup()

        is_local = os.getenv("IS_LOCAL", "false").lower() == "true"

        if not is_local:
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_context.load_cert_chain(
                certfile='/etc/letsencrypt/live/smartgadgetstore.live/fullchain.pem',
                keyfile='/etc/letsencrypt/live/smartgadgetstore.live/privkey.pem'
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
