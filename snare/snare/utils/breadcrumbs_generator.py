import os
import hashlib
import json
import logging
import random
import requests
import re

from snare.utils.snare_helpers import print_color
from snare.config import SnareConfig

class BreadcrumbsGenerator:
    def __init__(self, 
                 page_dir, 
                 meta):
        self.logger = logging.getLogger(__name__)
        self.page_dir = page_dir
        self.meta = meta
        self.used_canarytoken = []
        self.api_endpoint = SnareConfig.get("BREADCRUMB", "API-ENDPOINT")
        self.api_key = SnareConfig.get("BREADCRUMB", "API-KEY")
        self.llm_parameters = SnareConfig.get("BREADCRUMB", "LLM-PARAMETERS")
        self.honeytoken_path = "/opt/snare/honeytokens/Honeytokens.txt"

    def generate_breadcrumbs(self):
        """
        Generates breadcrumbs for the given types.
        Always cleans up the 404 and robots.txt files regardless of generation flag.
        """
        breadcrumb_types = SnareConfig.get("BREADCRUMB", "TYPES")

        for breadcrumb in breadcrumb_types:
            breadcrumb_types = breadcrumb.strip()
            if breadcrumb == 'robots':
                self.generate_robots_breadcrumb()
            elif breadcrumb == '404_page':
                self.generate_404_breadcrumb()
            elif breadcrumb == 'html_comments':
                self.generate_html_comments_breadcrumb()
            else:
                print_color("Breadcrumb type '{}' is not supported yet.".format(breadcrumb), "WARNING")

    def generate_robots_breadcrumb(self):
        """
        Generates or refreshes robots.txt with realistic bait paths.
        """
        file_name = "robots.txt"
        hash_name = self._make_filename(file_name)
        robots_path = os.path.join(self.page_dir, hash_name)

        # check if /robots.txt is in meta.json — if not, add it
        abs_url = "/robots.txt"
        if abs_url not in self.meta:
            self.meta[abs_url] = {
                "hash": hash_name,
                "content_type": "text/plain"
            }
        else:
            # already exists — clear old content
            with open(robots_path, "w") as f:
                f.write("")

        # load bait from honeytokens
        honeytoken_path = "/opt/snare/honeytokens/Honeytokens.txt"
        bait_lines = []
        bait_sample = []
        if os.path.exists(honeytoken_path):
            with open(honeytoken_path, "r") as f:
                tokens = [line.strip() for line in f if line.strip()]
                canarytokens = [token for token in tokens if token.endswith(('.pdf', '.xlsx', '.docs'))]
                non_canarytokens = [token for token in tokens if token not in canarytokens]
                
                # Select one canarytoken and mark it as used
                if canarytokens:
                    chosen_canarytoken = random.choice([token for token in canarytokens if token not in self.used_canarytoken])
                    self.used_canarytoken.append(chosen_canarytoken)
                    bait_lines.append(f"Disallow: /{chosen_canarytoken}")

                # Add other non-canarytokens
                bait_lines.extend([f"Disallow: /{token}" for token in non_canarytokens])

        lines = [
            "User-agent: *",
            ""
        ] + bait_lines + [
            "Disallow: /private/",
            "Disallow: /admin/",
            "Disallow: /admin/login.php",
            "",
            "Sitemap: https://smartgadgetstore.live/sitemap.xml"
        ]

        # write the new content
        with open(robots_path, "w") as f:
            f.write("\n".join(lines))

        # save meta.json (in case it was just added)
        meta_json_path = os.path.join(self.page_dir, "meta.json")
        with open(meta_json_path, "w") as meta_file:
            json.dump(self.meta, meta_file, indent=4)

        if bait_sample:
            self.logger.debug(f"Added breadcrumbs in robots.txt with bait: {bait_sample}")
        else:
            self.logger.debug("Added breadcrumbs in robots.txt (no honeytokens found)")

    def generate_404_breadcrumb(self):
        """
        Rewrites the 404 page identified by '/status_404' in meta with a breadcrumb line
        generated using an LLM and one random honeytoken.
        If not found, creates the entry and file.
        """
        abs_url = "/status_404"
        hash_name = self.meta.get(abs_url, {}).get("hash")

        # If not found in meta, create it
        if not hash_name:
            hash_name = self._make_filename(abs_url)
            self.meta[abs_url] = {
                "hash": hash_name,
                "content_type": "text/html"
            }

            # Save updated meta.json
            meta_json_path = os.path.join(self.page_dir, "meta.json")
            with open(meta_json_path, "w") as meta_file:
                json.dump(self.meta, meta_file, indent=4)
            print_color(f"Breadcrumbing: Created new meta entry for '{abs_url}'", "INFO")

        html_path = os.path.join(self.page_dir, hash_name)

        # If file doesn't exist, create a basic HTML structure
        if not os.path.exists(html_path):
            with open(html_path, "w") as f:
                f.write("<html><body></body></html>")

        # Read current content
        with open(html_path, "r") as f:
            html_content = f.read()

        # Load honeytokens
        if not os.path.exists(self.honeytoken_path):
            print_color("No Honeytokens.txt found. Cannot generate breadcrumb.", "WARNING")
            return

        with open(self.honeytoken_path, "r") as f:
            tokens = [line.strip() for line in f if line.strip()]

        # Filter out already used tokens
        available_tokens = [token for token in tokens if token not in self.used_canarytoken]
        if not available_tokens:
            print_color("No available honeytokens for 404 breadcrumb.", "WARNING")
            return

        chosen_token = random.choice(available_tokens)
        self.used_canarytoken.append(chosen_token)

        # Generate breadcrumb from LLM
        breadcrumb_line = self._generate_404_content_from_llm(chosen_token)

        # Remove old breadcrumb if it exists
        html_content = html_content.replace("<p>This is a breadcrumb.</p>", "")
        if "</body>" in html_content:
            html_content = html_content.replace("</body>", breadcrumb_line + "\n</body>")
        else:
            html_content += "\n" + breadcrumb_line

        # Save updated HTML
        with open(html_path, "w") as f:
            f.write(html_content)

        self.logger.debug(f"Updated 404 page with breadcrumb referencing '/{chosen_token}'")

    def _generate_404_content_from_llm(self, honeytoken):
        prompt = SnareConfig.get("BREADCRUMB", "PROMPT-404-ERROR").replace("{honeytoken}", honeytoken)
        response = requests.post(
            self.api_endpoint,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "inputs": prompt,
                "parameters": self.llm_parameters
            }
        )

        if response.status_code != 200:
            print_color(f"HuggingFace API Error {response.status_code}: {response.text}", "WARNING")
            return f"<p>Check /{honeytoken} for debug info.</p>"

        try:
            raw = response.json()[0]["generated_text"].strip()

            # Remove preamble text like "Here's a possible solution:"
            if ":" in raw:
                raw = raw.split(":", 1)[1].strip()

            # Ensure the honeytoken path is mentioned
            if f"/{honeytoken}" not in raw:
                raw += f" (see /{honeytoken})"

            # Wrap in a clean <p> tag if not already
            if not raw.startswith("<p>"):
                raw = f"<p>{raw}</p>"

            return raw

        except (KeyError, IndexError, TypeError):
            return f"<p>Access /{honeytoken} for diagnostics.</p>"

    def generate_html_comments_breadcrumb(self):
        """
        Safely injects a breadcrumb HTML comment below a randomly selected existing HTML comment in the file.
        """
        abs_url = "/index.html"
        hash_name = self.meta.get(abs_url, {}).get("hash")

        if not hash_name:
            print_color("Meta entry for /index.html not found.", "WARNING")
            return

        html_path = os.path.join(self.page_dir, hash_name)
        if not os.path.exists(html_path):
            print_color(f"index.html not found at {html_path}. Skipping injection.", "WARNING")
            return

        with open(html_path, "r") as f:
            html_content = f.read()

        # Find all HTML comments
        all_comments = re.findall(r'<!--.*?-->', html_content)
        if not all_comments:
            print_color("No HTML comments found in the file.", "WARNING")
            return

        # Pick a random comment to inject after
        anchor_comment = random.choice(all_comments)

        if not os.path.exists(self.honeytoken_path):
            print_color("Honeytokens.txt not found.", "WARNING")
            return

        with open(self.honeytoken_path, "r") as f:
            tokens = [line.strip() for line in f if line.strip()]
            
        # Filter out already used tokens
        available_tokens = [token for token in tokens if token not in self.used_canarytoken]
        if not available_tokens:
            print_color("No available honeytokens for HTML comments.", "WARNING")
            return

        # Select a unique token for the HTML comment
        chosen_token = random.choice(available_tokens)
        self.used_canarytoken.append(chosen_token)

        # Generate the HTML comment
        comment = self._generate_html_comment_from_llm(chosen_token)

        # Inject the generated comment after the anchor comment
        html_content = html_content.replace(anchor_comment, anchor_comment + "\n" + comment)

        with open(html_path, "w") as f:
            f.write(html_content)

        self.logger.debug(f"Injected breadcrumbs in HTML comment after '{anchor_comment}' for '/{chosen_token}'")


    def _generate_html_comment_from_llm(self, honeytoken):
        prompt = SnareConfig.get("BREADCRUMB", "PROMPT-HTML-COMMENT").replace("{honeytoken}", honeytoken)
        response = requests.post(
            self.api_endpoint,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "inputs": prompt,
                "parameters": self.llm_parameters
            }
        )

        if response.status_code != 200:
            print_color(f"Failed to fetch LLM comment: {response.status_code}", "WARNING")
            return f"<!-- dev note /{honeytoken} -->"

        try:
            text = response.json()[0]["generated_text"].strip()

            # Clean invalid syntax
            text = text.split(":", 1)[1].strip() if ":" in text else text
            text = text.replace("--", "–").replace("\n", " ").strip()

            if f"/{honeytoken}" not in text:
                text += f" /{honeytoken}"

            return f"<!-- {text} -->"
        except Exception:
            return f"<!-- dev ref /{honeytoken} -->"

    @staticmethod
    def _make_filename(file_name):
        # Compute the MD5 hash of the content
        m = hashlib.md5()  
        m.update(file_name.encode("utf-8"))
        hash_name = m.hexdigest()

        return hash_name
    