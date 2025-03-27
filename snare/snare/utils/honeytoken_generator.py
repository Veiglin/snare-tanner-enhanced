import os
import re
import json
import time
import random
import hashlib
import requests

from snare.utils.snare_helpers import print_color


class HoneytokensGenerator:
    def __init__(self, page_dir, log_dir, meta, hf_token, logger=print_color):
        self.page_dir = page_dir
        self.log_dir = log_dir
        self.meta = meta
        self.hf_token = hf_token
        self.logger = logger
        self.marker = "__honeypot_honeytokens_marker__"
        self.model = "mistralai/Mistral-7B-Instruct-v0.1"

        os.makedirs(self.page_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)

        self.meta_path = os.path.join(self.page_dir, "meta.json")
        self.log_path = os.path.join(self.log_dir, "Honeytokens.txt")

        self.content_types = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".xls": "application/vnd.ms-excel",
            ".db": "application/octet-stream",
            ".sql": "application/sql",
            ".zip": "application/zip",
            ".bak": "application/octet-stream",
            ".tar.gz": "application/gzip"
        }

    def generate(self):
        prompt = (
            "You are generating bait filenames for a website called SmartGadgetStore.live, which sells smart gadgets and electronics online. "
            "Generate 5 realistic, code-friendly filenames (no spaces or special characters) that might contain sensitive internal data. "
            "Examples include inventory backups, customer exports, admin data, supplier lists, or device configuration dumps. "
            "Use believable extensions like .pdf, .db, .sql, .zip, or .bak. "
            f"Ensure all filenames look authentic and vary slightly each time.\n"
            f"# Session ID: {random.randint(1000,9999)}_{int(time.time())}"
        )

        response = requests.post(
            f"https://api-inference.huggingface.co/models/{self.model}",
            headers={"Authorization": f"Bearer {self.hf_token}"},
            json={
                "inputs": prompt,
                "parameters": {
                    "temperature": 0.9,
                    "do_sample": True,
                    "top_p": 0.95,
                    "top_k": 50,
                    "max_new_tokens": 100
                }
            }
        )

        if response.status_code != 200:
            self.logger(f"❌ Hugging Face API failed: {response.status_code} — {response.text}", "FAIL")
            return

        result = response.json()
        text = result[0]["generated_text"] if isinstance(result, list) and "generated_text" in result[0] else ""
        filenames = self._extract_clean_filenames(text)

        self.logger("🧠 Raw LLM Response:\n" + text.strip(), "INFO")
        self.logger("📂 Cleaned Filenames:\n" + "\n".join(f" - {name}" for name in filenames), "SUCCESS")

        self._create_honeytokens(filenames)
        self._write_honeytoken_log()

    def _extract_clean_filenames(self, text):
        lines = text.strip().split("\n")
        cleaned = []

        for line in lines:
            line = re.sub(r"^[-*\s#\d\.\)]*\s*", "", line)
            line = re.sub(r"^.*?:\s*", "", line)
            line = line.replace(" ", "_")
            line = re.sub(r"[^a-zA-Z0-9_\.\-]", "", line)
            if re.match(r".+\.(pdf|docx|xls|db|sql|zip|bak|tar\.gz)$", line):
                cleaned.append(line)

        return cleaned

    def _md5_hash(self, text):
        return hashlib.md5(text.encode("utf-8")).hexdigest().lower()

    def _create_honeytokens(self, filenames):
        # Load or create meta
        if os.path.exists(self.meta_path):
            with open(self.meta_path, "r") as f:
                meta = json.load(f)
        else:
            meta = {}

        # Insert marker if missing
        if self.marker not in meta:
            meta[self.marker] = "DO NOT REMOVE — all entries after this are auto-generated honeytokens"

        for name in filenames:
            hash_val = self._md5_hash(name)
            ext = os.path.splitext(name)[1]
            content_type = self.content_types.get(ext.lower(), "application/octet-stream")

            dummy_path = os.path.join(self.page_dir, hash_val)
            if not os.path.exists(dummy_path):
                with open(dummy_path, "wb") as f:
                    f.write(b"This is a honeypot file. Access is monitored.\n")

            meta[f"/{name}"] = {
                "content_type": content_type,
                "hash": hash_val.upper()
            }

        # Save updated meta
        with open(self.meta_path, "w") as f:
            json.dump(meta, f, indent=4)

        self.logger(f"✅ Created {len(filenames)} honeytoken files in {self.page_dir}", "SUCCESS")

    def _write_honeytoken_log(self):
        if not os.path.exists(self.meta_path):
            self.logger("⚠️ meta.json not found. Skipping Honeytokens.txt log.", "WARNING")
            return

        with open(self.meta_path, "r") as f:
            meta = json.load(f)

        logging = False
        filenames = []

        for key in meta.keys():
            if logging:
                filenames.append(key.strip("/"))
            if key == self.marker:
                logging = True

        with open(self.log_path, "w") as f:
            for name in filenames:
                f.write(name + "\n")

        self.logger(f"📝 Honeytokens.txt updated with {len(filenames)} filenames at {self.log_path}", "INFO")

    def cleanup(self):
        if not os.path.exists(self.meta_path):
            self.logger("⚠️ meta.json not found. Nothing to clean.", "WARNING")
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

        self.logger(f"🧹 Deleted {len(deleted_files)} honeytoken files and cleaned meta.json.", "INFO")
