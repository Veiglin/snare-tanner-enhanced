import os
import hashlib
import json
import random
import requests
import re



from snare.utils.snare_helpers import print_color

class BreadcrumbsGenerator:
    def __init__(self, page_dir, meta, breadcrumb=None,   
        self.page_dir = page_dir
        self.meta = meta
        self.breadcrumb = breadcrumb or []
        self.   =   
        self.model = "mistralai/Mistral-7B-Instruct-v0.1"
        self.honeytoken_path = "/opt/snare/honeytokens/Honeytokens.txt"

    
    def generate_breadcrumbs(self):
        """
        Generates breadcrumbs for the given types.
        Always cleans up the 404 and robots.txt files regardless of generation flag.
        """
        self.clean_404_breadcrumb()
        # self.clean_html_comments_breadcrumb()

        for breadcrumb in self.breadcrumb:
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
        hash_name = self.make_filename(file_name)
        robots_path = os.path.join(self.page_dir, hash_name)

        # Check if /robots.txt is in meta.json — if not, add it
        abs_url = "/robots.txt"
        if abs_url not in self.meta:
            self.meta[abs_url] = {
                "hash": hash_name,
                "content_type": "text/plain"
            }
        else:
            # Already exists — clear old content
            with open(robots_path, "w") as f:
                f.write("")

        # Load bait from honeytokens
        honeytoken_path = "/opt/snare/honeytokens/Honeytokens.txt"
        bait_lines = []
        bait_sample = []
        if os.path.exists(honeytoken_path):
            with open(honeytoken_path, "r") as f:
                tokens = [line.strip() for line in f if line.strip()]
                if tokens:
                    bait_sample = random.sample(tokens, min(len(tokens), 3))
                    bait_lines = [f"Disallow: /{token}" for token in bait_sample]

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

        # Write the new content
        with open(robots_path, "w") as f:
            f.write("\n".join(lines))

        # Save meta.json (in case it was just added)
        meta_json_path = os.path.join(self.page_dir, "meta.json")
        with open(meta_json_path, "w") as meta_file:
            json.dump(self.meta, meta_file, indent=4)

        if bait_sample:
            print_color(f"Breadcrumbing: Refreshed robots.txt with bait: {bait_sample}", "SUCCESS")
        else:
            print_color("Breadcrumbing: Refreshed robots.txt (no honeytokens found)", "SUCCESS")


    def generate_404_breadcrumb(self):
        """
        Rewrites the 404 page identified by '/status_404' in meta with a breadcrumb line
        generated using an LLM and one random honeytoken.
        If not found, creates the entry and file.
        """
        import requests  # ensure this is imported at the top

        abs_url = "/status_404"
        hash_name = self.meta.get(abs_url, {}).get("hash")

        # If not found in meta, create it
        if not hash_name:
            hash_name = self.make_filename(abs_url)
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
            print_color("⚠️ No Honeytokens.txt found. Cannot generate breadcrumb.", "WARNING")
            return

        with open(self.honeytoken_path, "r") as f:
            tokens = [line.strip() for line in f if line.strip()]

        if not tokens:
            print_color("⚠️ Honeytokens.txt is empty. Cannot generate breadcrumb.", "WARNING")
            return

        chosen_token = random.choice(tokens)

        # Generate breadcrumb from LLM
        breadcrumb_line = self._generate_breadcrumb_from_llm(chosen_token)

        # Remove old breadcrumb if it exists
        html_content = html_content.replace("<p>This is a breadcrumb.</p>", "")
        if "</body>" in html_content:
            html_content = html_content.replace("</body>", breadcrumb_line + "\n</body>")
        else:
            html_content += "\n" + breadcrumb_line

        # Save updated HTML
        with open(html_path, "w") as f:
            f.write(html_content)

        print_color(f"Breadcrumbing: Updated 404 page with breadcrumb referencing '/{chosen_token}'", "SUCCESS")


    def _generate_breadcrumb_from_llm(self, honeytoken):
        prompt = (
            f"Write a short HTML bait line (in a <p> tag) that subtly hints at an internal file located at /{honeytoken}. "
            f"It should look like something a developer accidentally left in, referencing the file path naturally."
            f"Your goal is to lead a potential attacker to believe that this is a legitimate file path. "
        )

        response = requests.post(
            f"https://api-inference.huggingface.co/models/{self.model}",
            headers={"Authorization": f"Bearer {self.  
            json={
                "inputs": prompt,
                "parameters": {
                    "temperature": 0.8,
                    "do_sample": True,
                    "top_p": 0.9,
                    "top_k": 50,
                    "max_new_tokens": 60,
                    "return_full_text": False
                }
            }
        )

        if response.status_code != 200:
            print_color(f"⚠️ LLM API error {response.status_code}: {response.text}", "WARNING")
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




    def clean_404_breadcrumb(self):
        """
        Removes any existing breadcrumb line from the /status_404 page.
        """
        abs_url = "/status_404"
        hash_name = self.meta.get(abs_url, {}).get("hash")

        if not hash_name:
            # Still create the meta entry for consistency
            hash_name = self.make_filename(abs_url)
            self.meta[abs_url] = {
                "hash": hash_name,
                "content_type": "text/html"
            }
            meta_json_path = os.path.join(self.page_dir, "meta.json")
            with open(meta_json_path, "w") as meta_file:
                json.dump(self.meta, meta_file, indent=4)
            print_color(f"Breadcrumbing: Created new meta entry for '{abs_url}'", "INFO")

        html_path = os.path.join(self.page_dir, hash_name)

        if not os.path.exists(html_path):
            with open(html_path, "w") as f:
                f.write("<html><body></body></html>")
            return

        # Read and clean the file
        with open(html_path, "r") as f:
            html_content = f.read()

        breadcrumb = "<p>This is a breadcrumb.</p>"
        if breadcrumb in html_content:
            html_content = html_content.replace(breadcrumb, "")
            with open(html_path, "w") as f:
                f.write(html_content)
            print_color("Breadcrumbing: Removed old breadcrumb from /status_404 page.", "INFO")


    def generate_html_comments_breadcrumb(self):
        """
        Safely injects a breadcrumb HTML comment below a randomly selected existing HTML comment in the file.
        """
        abs_url = "/index.html"
        hash_name = self.meta.get(abs_url, {}).get("hash")

        if not hash_name:
            print_color("⚠️ Meta entry for /index.html not found.", "WARNING")
            return

        html_path = os.path.join(self.page_dir, hash_name)
        if not os.path.exists(html_path):
            print_color(f"⚠️ index.html not found at {html_path}. Skipping injection.", "WARNING")
            return

        with open(html_path, "r") as f:
            html_content = f.read()

        # Find all HTML comments
        all_comments = re.findall(r'<!--.*?-->', html_content)
        if not all_comments:
            print_color("⚠️ No HTML comments found in the file.", "WARNING")
            return

        # Pick a random comment to inject after
        anchor_comment = random.choice(all_comments)

        if not os.path.exists(self.honeytoken_path):
            print_color("⚠️ Honeytokens.txt not found.", "WARNING")
            return

        with open(self.honeytoken_path, "r") as f:
            tokens = [line.strip() for line in f if line.strip()]
        if not tokens:
            print_color("⚠️ Honeytokens.txt is empty.", "WARNING")
            return

        chosen_token = random.choice(tokens)
        comment = self._generate_html_comment_from_llm(chosen_token)

        # Inject the generated comment after the anchor comment
        html_content = html_content.replace(anchor_comment, anchor_comment + "\n" + comment)

        with open(html_path, "w") as f:
            f.write(html_content)

        print_color(f"Breadcrumbing: Injected comment after '{anchor_comment}' for '/{chosen_token}'", "SUCCESS")




    def _generate_html_comment_from_llm(self, honeytoken):
        prompt = (
            f"Write a realistic one-line HTML comment like a developer's note. "
            f"It should mention /{honeytoken} as if it's a config file or temporary log. "
            f"Do NOT include HTML tags or '--'. Make it look like leftover debug info."
        )

        response = requests.post(
            f"https://api-inference.huggingface.co/models/{self.model}",
            headers={"Authorization": f"Bearer {self.  
            json={
                "inputs": prompt,
                "parameters": {
                    "temperature": 0.8,
                    "do_sample": True,
                    "top_p": 0.9,
                    "top_k": 50,
                    "max_new_tokens": 60,
                    "return_full_text": False
                }
            }
        )

        if response.status_code != 200:
            print_color(f"⚠️ Failed to fetch LLM comment: {response.status_code}", "WARNING")
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



    def clean_html_comments_breadcrumb(self):
        """
        Removes any HTML comment in /index.html that references a honeytoken path.
        """
        abs_url = "/index.html"
        hash_name = self.meta.get(abs_url, {}).get("hash")
        if not hash_name:
            return

        html_path = os.path.join(self.page_dir, hash_name)
        if not os.path.exists(html_path):
            return

        with open(html_path, "r") as f:
            html_content = f.read()

        # Remove any HTML comment with a slash path inside (e.g., /logs/file.sql)
        cleaned = re.sub(r"<!--.*?/[a-zA-Z0-9_\-/]+\.\w+.*?-->\n?", "", html_content, flags=re.DOTALL)

        if cleaned != html_content:
            with open(html_path, "w") as f:
                f.write(cleaned)
            print_color("Breadcrumbing: Removed old HTML comment breadcrumb from index.html", "INFO")






    @staticmethod
    def make_filename(file_name):
        # Compute the MD5 hash of the content
        m = hashlib.md5()  
        m.update(file_name.encode("utf-8"))
        hash_name = m.hexdigest()

        return hash_name