import os
import re
import json
import time
import random
import hashlib
import requests
from typing import Optional
import requests

from snare.utils.snare_helpers import print_color
from snare.config import SnareConfig

TOKENS_URL = 'https://canarytokens.org'
TOKENS_DOWNLOAD_URL = 'https://canarytokens.org/d3aece8093b71007b5ccfedad91ebb11/download'

class HoneytokensGenerator:
    def __init__(self, 
                 page_dir, 
                 meta):
        self.page_dir = page_dir
        self.meta = meta
        self.api_endpoint = SnareConfig.get("HONEYTOKEN", "API-ENDPOINT")
        self.api_key = SnareConfig.get("HONEYTOKEN", "API-KEY")
        self.llm_parameters = SnareConfig.get("HONEYTOKEN", "LLM-PARAMETERS")
        if os.getenv("IS_LOCAL") == "true":
            self.webhook_url = SnareConfig.get("HONEYTOKEN", "WEBHOOK-URL")
        else:
            self.webhook_url = "http://128.251.49.251:5003/webhook"
        self.marker = "__honeypot_honeytokens_marker__"
        # 🔒 Hardcoded log directory
        self.track_dir = os.path.join("/opt/snare", "honeytokens")
        self.track_path = os.path.join(self.track_dir, "Honeytokens.txt")
        os.makedirs(self.page_dir, exist_ok=True)
        os.makedirs(self.track_dir, exist_ok=True)
        self.meta_path = os.path.join(self.page_dir, "meta.json")
        self.meta_content_types = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".xls": "application/vnd.ms-excel",
            ".db": "application/octet-stream",
            ".sql": "application/sql",
            ".zip": "application/zip",
            ".bak": "application/octet-stream",
            ".tar.gz": "application/gzip"
        }
        self.canary_content_types = {
            ".pdf": "adobe_pdf",
            ".docx": "ms_word",
            ".xlsx": "ms_excel"
        }

    def generate_filenames(self):

        session_id = f"{random.randint(1000,9999)}_{int(time.time())}"
        prompt = SnareConfig.get("HONEYTOKEN", "PROMPT").replace("{session_id}", session_id)
        response = requests.post(
            self.api_endpoint,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "inputs": prompt,
                "parameters": self.llm_parameters
            }
        )
        if response.status_code != 200:
            print_color(f"❌ LLM API failed: {response.status_code} — {response.text}", "FAIL")
            return
        result = response.json()
        text = result[0]["generated_text"] if isinstance(result, list) and "generated_text" in result[0] else ""
        print_color("🧠 Raw LLM Response:\n" + text.strip(), "INFO")

        filenames = self._extract_clean_filenames(text)
        print_color("📂 Cleaned Filenames:\n" + "\n".join(f" - {name}" for name in filenames), "SUCCESS")
        return filenames

    def _extract_clean_filenames(self, text):
        lines = text.strip().split("\n")
        cleaned = []
        for line in lines:
            line = re.sub(r"^[-*\s#\d\.\)]*\s*", "", line)
            line = re.sub(r"^.*?:\s*", "", line)
            line = line.replace(" ", "_")
            line = re.sub(r"[^a-zA-Z0-9_\.\-]", "", line)
            if re.match(r".+\.(pdf|docx|xlsx|db|sql|zip|bak|tar\.gz)$", line):
                cleaned.append(line)
        return cleaned

    def _md5_hash(self, text):
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    def create_honeytokens(self, filenames):
        # Load or create meta
        if os.path.exists(self.meta_path):
            with open(self.meta_path, "r") as f:
                meta = json.load(f)
        else:
            meta = {}

        # Insert marker if missing
        if self.marker not in meta:
            meta[self.marker] = "DO NOT REMOVE — all entries after this are auto-generated honeytokens"

        # Pick a session path prefix once
        prefix = random.choice(["wp-admin", "admin", "includes", "cgi-bin", "private", "search", "action", "modules", "filter\tips", "comment\reply", "node\add"])
        self.generated_paths = []  # store full paths like 'logs/vault2022.db'
        for name in filenames:
            full_path = os.path.join(prefix, name).replace("\\", "/")  # ensures it's slash-separated
            hash_val = self._md5_hash(full_path)
            ext = os.path.splitext(name)[1]

            content_type = self.meta_content_types.get(ext.lower(), "application/octet-stream")
            #dummy_path = os.path.join(self.page_dir, hash_val.upper())
            #if not os.path.exists(dummy_path):
            #    with open(dummy_path, "wb") as f:
            #        f.write(b"This is a honeypot file. Access is monitored.\n")

            meta[f"/{full_path}"] = {
                "content_type": content_type,
                "hash": hash_val
            }
            self.generated_paths.append(full_path)

        # Save updated meta
        with open(self.meta_path, "w") as f:
            json.dump(meta, f, indent=4)

        print_color(f"✅ Created {len(filenames)} honeytoken files in {self.page_dir} under /{prefix}/", "SUCCESS")

    def write_trackfile(self):
        if not hasattr(self, "generated_paths"):
            print_color("⚠️ No honeytokens generated in this session. Skipping log update.", "WARNING")
            return
        with open(self.track_path, "w") as f:
            for name in self.generated_paths:
                f.write(name + "\n")

        print_color(f"📝 Honeytokens.txt updated with {len(self.generated_paths)} filenames at {self.track_path}", "INFO")


    def cleanup_honeytokens(self):
        if not os.path.exists(self.meta_path):
            print_color("⚠️ meta.json not found. Nothing to clean.", "WARNING")
            return
        with open(self.meta_path, "r") as f:
            meta = json.load(f)
        updated_meta = {}
        deleting = False
        deleted_files = []

        for key, entry in meta.items():
            if deleting:
                hash_val = entry.get("hash", "").lower()
                token_path = os.path.join(self.page_dir, hash_val)
                if os.path.exists(token_path):
                    os.remove(token_path)
                    deleted_files.append(hash_val)
            else:
                updated_meta[key] = entry
            if key == self.marker:
                deleting = True

        with open(self.meta_path, "w") as f:
            json.dump(updated_meta, f, indent=4)

        # print_color(f"🧹 Deleted {len(deleted_files)} honeytoken files and cleaned meta.json.", "INFO")

    def generate_canarytokens(self):

        # Load Honeytokens.txt
        if not os.path.exists(self.track_path):
            print_color("⚠️ Honeytokens.txt not found. Nothing to generate.", "WARNING")
            return
        with open(self.track_path, "r") as f:
            honeytokens = f.read().splitlines()
        
        # Generate canarytokens for pdf, xlsx, docx
        # go through the honeytokens and generate a canarytoken for those that are pdf, xlsx, docx
        for token in honeytokens:
            # check if the token is a pdf, xlsx, docx
            if token.endswith('.pdf') or token.endswith('.xlsx') or token.endswith('.docx'):
                # generate the canarytoken by calling the generate_token function for 
                token_type = self.canary_content_types.get((os.path.splitext(token)[1]).lower())
                print_color(f"{self.webhook_url}", "SUCCESS")
                canarytoken = self.generate_token(token_type, token + " - Triggered", webhook=self.webhook_url)
                if canarytoken:
                    print_color(f"✅ Generated canarytoken for {token}: {canarytoken}", "SUCCESS")

                    # download the canarytoken file
                    canarytoken_content = self._downloaded_token_file(token_type, canarytoken['auth_token'], canarytoken['token'])

                    # save the canarytoken file in the hashed filename within the page_dir
                    hashed_filename = self._md5_hash(token)
                    hashed_filename = os.path.join(self.page_dir, hashed_filename)
                    with open(hashed_filename, "wb") as f:
                        f.write(canarytoken_content)
                    print_color(f"✅ Saved canarytoken file as {hashed_filename}", "SUCCESS")
                else:
                    print_color(f"❌ Failed to generate canarytoken for {token}", "FAIL")
            else:
                print_color(f"⚠️ Skipping non-supported file type: {token}", "WARNING")

    def generate_token(self, type: str, memo : str, webhook: str = '') -> Optional[str]:
        '''
        Returns a web bug token URL given an email and memo
        '''
        req_data = {
            'type': type,
            'memo': memo,
            'webhook_url': webhook
        }
        res = requests.post(TOKENS_URL + '/generate', data=req_data)
        if res.status_code != 200:
            print_color(f"Error: {res.status_code} - {res.text}", "ERROR")
            return None
        return res.json()

    def _downloaded_token_file(self, type: str, auth: str, token: str) -> None:

        print_color(type, "INFO")
        # Map the file type to the correct fmt
        file_extensions = {
            'adobe_pdf': 'pdf',
            'ms_word': 'msword',
            'ms_excel': 'msexcel',
        }

        fmt = file_extensions.get(type)
        if not fmt:
            print_color(f"Unsupported file type: {type}", "ERROR")
            return None
        
        # Define the download URL parameters
        params = {
            'fmt': fmt,
            'auth': auth,
            'token': token
        }

        # Make the GET request to download the file
        response = requests.get(TOKENS_DOWNLOAD_URL, params=params, allow_redirects=True)

        # Check if the request was successful
        if response.status_code == 200:
            print_color(f"File content successfully downloaded", "INFO")
            return response.content
        else:
            print_color(f"Failed to download content: {response.status_code} - {response.text}", "ERROR")
    
