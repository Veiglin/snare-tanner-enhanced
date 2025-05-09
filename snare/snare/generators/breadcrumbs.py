import os
import hashlib
import json
import logging
import random
import requests
import re
import time

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
        self.api_provider = SnareConfig.get("BREADCRUMB", "API-PROVIDER")
        self.api_endpoint = SnareConfig.get("BREADCRUMB", "API-ENDPOINT")
        self.api_key = SnareConfig.get("BREADCRUMB", "API-KEY")
        self.llm_parameters = SnareConfig.get("BREADCRUMB", "LLM-PARAMETERS")
        self.track_dir = os.path.join("/opt/snare", "honeytokens")
        self.track_path = os.path.join(self.track_dir, "Honeytokens.txt")

    def generate_breadcrumbs(self):
        """
        Generates breadcrumbs for the given types.
        Always cleans up the 404 and robots.txt files regardless of generation flag.
        """
        breadcrumb_types = SnareConfig.get("BREADCRUMB", "TYPES")
        if not breadcrumb_types:
            print_color("No breadcrumb types specified. Skipping breadcrumb generation.", "WARNING")
            return

        for breadcrumb in breadcrumb_types:
            breadcrumb_types = breadcrumb.strip()
            if breadcrumb == 'robots':
                self.generate_robots_breadcrumb()
            elif breadcrumb == 'error_page':
                self.generate_error_pages_breadcrumb()
            elif breadcrumb == 'html_comments':
                self.generate_html_comments_breadcrumb()
            else:
                self.logger.info("Breadcrumb type '{}' is not supported yet.".format(breadcrumb), "WARNING")

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
        bait_lines = []
        if os.path.exists(self.track_path):
            with open(self.track_path, "r") as f:
                tokens = [line.strip() for line in f if line.strip()]
                canarytokens = [token for token in tokens if (token.lower()).endswith(('.pdf', '.xlsx', '.docx'))]
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

        if bait_lines:
            self.logger.debug(f"Added breadcrumbs in robots.txt with bait lines: {bait_lines}")
        else:
            self.logger.error("No bait lines added in Honeytokens.txt. Cannot generate robots.txt breadcrumbs.")

    def generate_error_pages_breadcrumb(self):
        """
        Rewrites the 404 page and one other random error page (400, 401, 403, 500)
        with a breadcrumb line generated using an LLM and one random honeytoken.
        Creates entries and files if they don't exist.
        """
        self._generate_status_breadcrumb("/status_404")

        # Pick one more random error page
        other_status_pages = ["/status_400", "/status_401", "/status_403", "/status_500"]
        random_status = random.choice(other_status_pages)
        self._generate_status_breadcrumb(random_status)
        print_color(f"Breadcrumbs generated for {random_status}", "INFO")

    def _generate_status_breadcrumb(self, abs_url):
        """
        Shared logic to generate a breadcrumb for a given status page (e.g., /status_404, /status_401).
        """
        hash_name = self.meta.get(abs_url, {}).get("hash")

        # If not found in meta, create it
        if not hash_name:
            hash_name = self._make_filename(abs_url)
            self.meta[abs_url] = {
                "hash": hash_name,
                "content_type": "text/html"
            }

            meta_json_path = os.path.join(self.page_dir, "meta.json")
            with open(meta_json_path, "w") as meta_file:
                json.dump(self.meta, meta_file, indent=4)
            self.logger.info(f"Breadcrumbing: Meta.json not found. Created new meta entry for '{abs_url}'", "INFO")

        html_path = os.path.join(self.page_dir, hash_name)

        if not os.path.exists(html_path):
            with open(html_path, "w") as f:
                f.write("<html><body></body></html>")

        with open(html_path, "r") as f:
            html_content = f.read()

        if not os.path.exists(self.track_path):
            self.logger.info("No Honeytokens.txt found. Cannot generate breadcrumb.", "WARNING")
            return

        with open(self.track_path, "r") as f:
            tokens = [line.strip() for line in f if line.strip()]

        available_tokens = [token for token in tokens if token not in self.used_canarytoken]
        if not available_tokens:
            self.logger.info("No available honeytokens for error page breadcrumbs. Choosing a random bait file")
            available_tokens = [token for token in tokens if token not in self.used_canarytoken and not (token.lower()).endswith(('.pdf', '.xlsx', '.docx'))]

        chosen_token = random.choice(available_tokens)
        self.used_canarytoken.append(chosen_token)

        breadcrumb_line = self._generate_error_page_content_from_llm(chosen_token)

        html_content = html_content.replace("<p>This is a breadcrumb.</p>", "")
        if "</body>" in html_content:
            html_content = html_content.replace("</body>", breadcrumb_line + "\n</body>")
        else:
            html_content += "\n" + breadcrumb_line

        with open(html_path, "w") as f:
            f.write(html_content)

        self.logger.debug(f"Updated {abs_url} with breadcrumb referencing '/{chosen_token}'")


    def _generate_error_page_content_from_llm(self, honeytoken):
        prompt = SnareConfig.get("BREADCRUMB", "PROMPT-ERROR-PAGE").replace("{honeytoken}", honeytoken)
        # Call the LLM API
        if self.api_provider == "huggingface":
            text = self._generate_huggingface_content(prompt)
        elif self.api_provider == "gemini":
            text = self._generate_gemini_content(prompt)
        try:
            # Remove preamble text like "Here's a possible solution:"
            if ":" in text:
                text = text.split(":", 1)[1].strip()

            # Ensure the honeytoken path is mentioned
            if f"/{honeytoken}" not in text:
                text += f" (see /{honeytoken})"

            # Wrap in a clean <p> tag if not already
            if not text.startswith("<p>"):
                text = f"<p>{text}</p>"
            return text

        except: # Fallback for a static response
            return f"<p>Access /{honeytoken} for diagnostics.</p>"
    
    def _generate_huggingface_content(self, prompt):
        """
        Generates content using the HuggingFace API.
        """
        response = requests.post(
            self.api_endpoint,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "inputs": prompt,
                "parameters": self.llm_parameters
            }
        )

        if response.status_code != 200:
            self.logger.error(f"HuggingFace API Error {response.status_code}: {response.text}")
            return None
        
        text = response.json()[0]["generated_text"].strip()
        return text
    
    def _generate_gemini_content(self, prompt):
        """
        Generates content using the Gemini API with retry logic (2 retries, 2 seconds delay).
        """
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": self.llm_parameters["temperature"],
                "topP": self.llm_parameters["top_p"],
                "topK": self.llm_parameters["top_k"],
                "maxOutputTokens": self.llm_parameters["max_new_tokens"]
            },
        }

        max_attempts = 3
        delay_seconds = 2

        for attempt in range(1, max_attempts + 1):
            try:
                response = requests.post(
                    f"{self.api_endpoint}:generateContent?key={self.api_key}",
                    headers=headers,
                    json=payload
                )
                if response.status_code == 200:
                    result = response.json()
                    return result["candidates"][0]["content"]["parts"][0]["text"]
                else:
                    print_color(f"Gemini API attempt {attempt} failed: {response.status_code} — {response.text}", "WARNING")
            except Exception as e:
                print_color(f"Gemini API attempt {attempt} raised exception: {str(e)}", "WARNING")

            if attempt < max_attempts:
                time.sleep(delay_seconds)

        print_color("Gemini API failed after multiple attempts.", "ERROR")
        return None

    def generate_html_comments_breadcrumb(self):
        """
        Safely injects a breadcrumb HTML comment below a randomly selected existing HTML comment in the file.
        """
        abs_url = "/index.html"
        hash_name = self.meta.get(abs_url, {}).get("hash")

        if not hash_name:
            self.logger.info("Meta entry for /index.html not found.", "WARNING")
            return

        html_path = os.path.join(self.page_dir, hash_name)
        if not os.path.exists(html_path):
            self.logger.info(f"index.html not found at {html_path}. Skipping injection.", "WARNING")
            return

        with open(html_path, "r") as f:
            html_content = f.read()

        # Find all HTML comments
        all_comments = re.findall(r'<!--.*?-->', html_content)
        if not all_comments:
            self.logger.info("No HTML comments found in the file.", "WARNING")
            return

        # Pick a random comment to inject after
        anchor_comment = random.choice(all_comments)

        if not os.path.exists(self.track_path):
            self.logger.info("Honeytokens.txt not found.", "WARNING")
            return

        with open(self.track_path, "r") as f:
            tokens = [line.strip() for line in f if line.strip()]
            
        # Filter out already used tokens
        available_tokens = [token for token in tokens if token not in self.used_canarytoken]
        if not available_tokens:
            self.logger.info("No available honeytokens for HTML comments breadcrumbs. Choosing a random bait file")
            # use non-canarytokens if no canarytokens are available
            available_tokens = [token for token in tokens if token not in self.used_canarytoken and not (token.lower()).endswith(('.pdf', '.xlsx', '.docx'))]

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
        if self.api_provider == "huggingface":
            text = self._generate_huggingface_content(prompt)
        elif self.api_provider == "gemini":
            text = self._generate_gemini_content(prompt)

        try:
            # Clean invalid syntax
            text = text.split(":", 1)[1].strip() if ":" in text else text
            text = text.replace("--", "–").replace("\n", " ").strip()

            if f"/{honeytoken}" not in text:
                text += f" /{honeytoken}"

            return f"<!-- {text} -->"
        except:
            return f"<!-- dev ref /{honeytoken} -->"

    @staticmethod
    def _make_filename(file_name):
        # Compute the MD5 hash of the content
        m = hashlib.md5()  
        m.update(file_name.encode("utf-8"))
        hash_name = m.hexdigest()

        return hash_name
    