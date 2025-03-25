import os
import json
import random
import requests
import hashlib

from snare.utils.snare_helpers import print_color

class HoneytokenFileGenerator:
    def __init__(self, page_dir):
        """
        Initializes the honeytoken generator.

        :param page_dir: The directory where meta.json and honeytoken files will be stored.
        """
        self.page_dir = page_dir
        self.meta_json_path = os.path.join(page_dir, "meta.json")

        # File extensions and their content types
        self.file_types = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".xls": "application/vnd.ms-excel",
            ".db": "application/octet-stream",
            ".sql": "application/sql",
            ".zip": "application/zip",
            ".bak": "application/octet-stream",
            ".tar.gz": "application/gzip"
        }

        # Prompts tailored by extension type
        self.file_prompts = {
            ".pdf": "that might contain exported reports, secrets, or documents",
            ".docx": "that could contain sensitive contracts, internal policies, or meeting notes",
            ".xls": "that might hold financial spreadsheets, salary data, or budgets",
            ".db": "for a database file that could store users, credentials, or internal logs",
            ".sql": "for an SQL dump of a database",
            ".zip": "for a zipped archive of internal tools, backups, or config files",
            ".bak": "that looks like a backup of important data",
            ".tar.gz": "for a compressed file containing logs or private server configs"
        }

        # Load or initialize meta.json
        if os.path.exists(self.meta_json_path):
            with open(self.meta_json_path, "r") as f:
                self.meta = json.load(f)
        else:
            self.meta = {}

    def pick_random_extension(self):
        return random.choice(list(self.file_types.keys()))

    def generate_filename_base(self, extension):
        context = self.file_prompts.get(extension, "")
        prompt = f"Generate a single realistic and suspicious-looking base filename (no extension) {context}. Use underscores instead of spaces."
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "mistral", "prompt": prompt}
        )
        raw_output = response.json().get("response", "").strip()
        return raw_output.split("\n")[0].strip("-•* ").strip().replace(" ", "_")

    @staticmethod
    def make_filename(file_name):
        m = hashlib.md5()
        m.update(file_name.encode("utf-8"))
        return m.hexdigest().upper()

    def update_meta_json(self, filename, hash_val, content_type):
        file_entry = f"/{filename}"
        self.meta[file_entry] = {
            "content_type": content_type,
            "hash": hash_val
        }

        with open(self.meta_json_path, "w") as f:
            json.dump(self.meta, f, indent=4)

    def create_dummy_file(self, hash_val, extension):
        filename = hash_val + extension
        filepath = os.path.join(self.page_dir, filename)
        with open(filepath, "wb") as f:
            f.write(b"This is a honeypot file. Access is monitored.\n")
        return filepath

    def create_honeytoken(self):
        ext = self.pick_random_extension()
        base_name = self.generate_filename_base(ext)
        full_name = base_name + ext
        hash_val = self.make_filename(full_name)
        content_type = self.file_types[ext]

        # Create the dummy file in the same dir
        dummy_path = self.create_dummy_file(hash_val, ext)
        print_color(f"Honeytoken: Created dummy file at '{dummy_path}'", "SUCCESS")

        # Update meta.json
        self.update_meta_json(full_name, hash_val, content_type)
        print_color(f"Honeytoken: Registered '{full_name}' → '{hash_val}' (type: {content_type})", "INFO")


# --- Example usage ---
if __name__ == "__main__":
    generator = HoneytokenFileGenerator(
        page_dir="docker/snare/dist/pages/WEBPAGE_hashed_copy"  # Update if path changes
    )
    generator.create_honeytoken()




# Hugging Face token:
# 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