import os
import re
import json
import time
import random
import logging
import hashlib
import requests
from typing import Optional
import requests
import zipfile
import shutil
import xml.etree.ElementTree as ET
from xml.sax import saxutils

from snare.utils.snare_helpers import print_color
from snare.config import SnareConfig

TOKENS_URL = 'https://canarytokens.org'
TOKENS_DOWNLOAD_URL = 'https://canarytokens.org/d3aece8093b71007b5ccfedad91ebb11/download'

class HoneytokensGenerator:
    def __init__(self, 
                 page_dir, 
                 meta):
        self.logger = logging.getLogger(__name__)
        self.page_dir = page_dir
        self.meta = meta
        self.api_provider = SnareConfig.get("HONEYTOKEN", "API-PROVIDER")
        self.api_endpoint = SnareConfig.get("HONEYTOKEN", "API-ENDPOINT")
        self.api_key = SnareConfig.get("HONEYTOKEN", "API-KEY")
        self.llm_parameters = SnareConfig.get("HONEYTOKEN", "LLM-PARAMETERS")
        if os.getenv("IS_LOCAL") == "true":
            self.webhook_url = SnareConfig.get("FEATURES", "WEBHOOK-URL-LOCAL")
        else:
            self.webhook_url = SnareConfig.get("FEATURES", "WEBHOOK-URL-DEPLOYMENT")
        self.marker = "__honeypot_honeytokens_marker__"
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
        """
        Generate filenames using the HuggingFace API.
        The filenames are generated using the prompt defined in the config file.
        """
        session_variants = [
            "Make them look realistic enough to fool a junior employee.",
            "Add a touch of urgency, as if the files were hastily generated before a data breach.",
            "Generate filenames that suggest high-value internal data.",
            "Add subtle typos to mimic real human-created filenames.",
            "Include hints that the files may contain payment or billing data.",
            "Mimic filenames you'd find in a disgruntled employee's backup folder.",
            "Make filenames that sound like they belong to a shady reseller.",
            "These files should appear to be exports from a misconfigured admin panel.",
            "Generate filenames a tech-savvy intern might name while cutting corners.",
            "Suggest these files were auto-exported by outdated internal tools.",
            "Use naming that implies secret supplier pricing or vendor deals.",
            "Pretend these were pulled during a compliance audit and never cleaned up.",
            "Make them look like reports prepared for a board meeting.",
            "Make filenames that feel 'too confidential' to be in a public directory.",
            "Give filenames that a hacker might think hold admin credentials.",
            "Mimic a leak from someone trying to expose shady practices.",
            "Make them just boring enough to avoid suspicion, but still clickable.",
            "Generate filenames that feel 'forgotten but dangerous'.",
            "Pretend these were copied quickly during an office shutdown.",
            "Include clues that this is from an older abandoned staging server.",
            "Generate as if the files were archived manually by someone non-technical.",
            "Imply customer PII may be inside, without being too obvious.",
            "These filenames should provoke curiosity and suspicion.",
            "Make the files look like juicy but plausible corporate documents.",
            "Name them like attachments from a whistleblower email."
        ]
        session = random.choice(session_variants)
        prompt = SnareConfig.get("HONEYTOKEN", "PROMPT-FILENAMES").replace("{session}", session)
        if self.api_provider == "huggingface":
            text = self._call_huggingface_api(prompt)
            self.logger.debug(f"Hugging Face API response: {text}")
        elif self.api_provider == "gemini":
            text = self._call_gemini_api(prompt)
            self.logger.debug(f"Gemini API response: {text}")
        filenames = self._extract_clean_filenames(text)
        print_color("Generated filenames:\n" + "\n".join(f" - {name}" for name in filenames), "SUCCESS")
        self.logger.debug(f"Generated filenames: {filenames}")
        return filenames
        
    def _call_huggingface_api(self, prompt):
        """
        Make an API call to Hugging Face.
        """
        api_endpoint = SnareConfig.get("HONEYTOKEN", "API-ENDPOINT")
        api_key = SnareConfig.get("HONEYTOKEN", "API-KEY")
        response = requests.post(
            api_endpoint,
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "inputs": prompt,
                "parameters": self.llm_parameters
            }
        )
        if response.status_code != 200:
            self.logger.error(f"Hugging Face API Failed: {response.status_code} — {response.text}")
            return None
        result = response.json()
        text = result[0]["generated_text"] if isinstance(result, list) and "generated_text" in result[0] else ""
        return text

    def _call_gemini_api(self, prompt):
        """
        Make an API call to Gemini with retry logic (2 retries, 2 seconds delay).
        """
        api_endpoint = SnareConfig.get("HONEYTOKEN", "API-ENDPOINT")
        api_key = SnareConfig.get("HONEYTOKEN", "API-KEY")
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
                    f"{api_endpoint}:generateContent?key={api_key}",
                    headers=headers,
                    json=payload
                )
                if response.status_code == 200:
                    result = response.json()
                    return result["candidates"][0]["content"]["parts"][0]["text"]
                else:
                    print_color(f"Gemini API attempt {attempt} failed: {response.status_code} — {response.text}")
            except Exception as e:
                print_color(f"Gemini API attempt {attempt} raised exception: {e}")

            if attempt < max_attempts:
                time.sleep(delay_seconds)

        self.logger.error("Gemini API failed after multiple attempts.")
        return None

    
    def _extract_clean_filenames(self, text):
        lines = text.strip().split("\n")
        cleaned = []
        for line in lines:
            # Remove numbered list prefixes (e.g., "5. ", "4. ")
            line = re.sub(r"^\d+\.\s*", "", line)
            # Extract text between ** and remove any trailing description in parentheses
            line = re.sub(r"\*\*(.+?)\*\*.*", r"\1", line)
            # Replace spaces with underscores
            line = line.replace(" ", "_")
            # Remove invalid characters
            line = re.sub(r"[^a-zA-Z0-9_\.\-]", "", line)
            if re.match(r".+\.(pdf|docx|xlsx|db|sql|zip|bak|tar\.gz)$", line): # Match valid filenames with specific extensions
                cleaned.append(line)
        return cleaned

    def _md5_hash(self, text):
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    def create_honeytokens(self, filenames):
        """
        Create honeytokens in the page_dir using the filenames provided.
        The honeytokens are created by hashing the filenames and saving them in the meta.json file.
        """
        # load or create meta
        if os.path.exists(self.meta_path):
            with open(self.meta_path, "r") as f:
                meta = json.load(f)
        else:
            meta = {}

        # insert marker if missing
        if self.marker not in meta:
            meta[self.marker] = "DO NOT REMOVE — all entries after this are auto-generated honeytokens"

        # pick a session path prefix once
        prefix = random.choice(["wp-admin", "admin", "includes", "cgi-bin", "private", "search", "action", "modules", "filter/tips", "comment/reply", "node/add"])
        self.generated_paths = []  # store full paths like 'logs/vault2022.db'
        for name in filenames:
            full_path = os.path.join(prefix, name).replace("\\", "/")  # ensures it's slash-separated
            hash_val = self._md5_hash(full_path)
            ext = os.path.splitext(name)[1]
            content_type = self.meta_content_types.get(ext.lower(), "application/octet-stream")
            meta[f"/{full_path}"] = {
                "content_type": content_type,
                "hash": hash_val
            }
            self.generated_paths.append(full_path)

        # save updated meta
        with open(self.meta_path, "w") as f:
            json.dump(meta, f, indent=4)

        self.logger.debug(f"Created {len(filenames)} bait and honeytoken files in {self.page_dir}: {self.generated_paths}")

    def write_trackfile(self):
        if not hasattr(self, "generated_paths"):
            print_color("No honeytokens generated in this session. Skipping log update.", "WARNING")
            return
        with open(self.track_path, "w") as f:
            for name in self.generated_paths:
                f.write(name + "\n")
                
        print_color(f"Honeytokens.txt updated with {len(self.generated_paths)} filenames at {self.track_path}", "INFO")

    def cleanup_honeytokens(self):
        if not os.path.exists(self.meta_path):
            print_color("meta.json not found. Nothing to clean.", "WARNING")
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
                
        # Remove the marker if it still exists in updated_meta
        if self.marker in updated_meta:
            del updated_meta[self.marker]

        with open(self.meta_path, "w") as f:
            json.dump(updated_meta, f, indent=4)

        print_color(f"Deleted {len(deleted_files)} honeytoken files and cleaned meta.json.", "INFO")

    def generate_canarytokens(self):
        """
        Generate canarytokens for the honeytokens in Honeytokens.txt
        The canarytokens are generated using the generate_token function and saved in the page_dir
        """
        # load Honeytokens.txt
        if not os.path.exists(self.track_path):
            print_color("Honeytokens.txt not found. Nothing to generate.", "WARNING")
            return
        with open(self.track_path, "r") as f:
            honeytokens = f.read().splitlines()
        
        # wait for 10 second before generating canarytokens to let the webhook be ready
        time.sleep(10)

        # go through the honeytokens and generate a canarytoken for those that are pdf, xlsx, docx
        for token in honeytokens:
            # check if the token is a pdf, xlsx, docx
            if token.endswith('.pdf') or token.endswith('.xlsx') or token.endswith('.docx'):
                # generate the canarytoken by calling the generate_token function for 
                token_type = self.canary_content_types.get((os.path.splitext(token)[1]).lower())
                canarytoken = self._generate_token(token_type, token + " - Triggered", webhook=self.webhook_url)
                if canarytoken:
                    print_color(f"Generated honeytoken for {token}: {canarytoken}", "SUCCESS")

                    # download the canarytoken file
                    canarytoken_content = self._downloaded_token_file(token_type, canarytoken['auth_token'], canarytoken['token'])

                    # save the canarytoken file in the hashed filename within the page_dir
                    hashed_filename = self._md5_hash(token)
                    hashed_filename = os.path.join(self.page_dir, hashed_filename)
                    with open(hashed_filename, "wb") as f:
                        f.write(canarytoken_content)
                    print_color(f"Saved honeytoken file as {hashed_filename}", "SUCCESS")
                    self.logger.debug(f"Created honeytoken for {token} saved as the hashed filename {hashed_filename}")

                    # Immediately inject content into newly downloaded token
                    if token.endswith(".docx"):
                        self._inject_docx(filepath=hashed_filename, honeytoken=token)
                    elif token.endswith(".xlsx"):
                        self._inject_xlsx(filepath=hashed_filename, honeytoken=token)

                else:
                    self.logger.error(f"Failed to generate canarytoken for {token}")
            else:
                print_color(f"Skipping non-supported file type: {token}", "WARNING")

    def _generate_token(self, type: str, memo : str, webhook: str = '') -> Optional[str]:
        req_data = {
            'type': type,
            'memo': memo,
            'webhook_url': webhook
        }
        res = requests.post(TOKENS_URL + '/generate', data=req_data)
        try:
            if res.status_code != 200:
                self.logger.error(f"Error: {res.status_code} - {res.text}")
                return None
            return res.json()
        except json.JSONDecodeError as e:
            print_color(f"Failed to generate honeytokens from canarytoken: {e}", "ERROR")
            return None

    def _downloaded_token_file(self, type: str, auth: str, token: str) -> bytes:
        # map the file type to the correct fmt
        file_extensions = {
            'adobe_pdf': 'pdf',
            'ms_word': 'msword',
            'ms_excel': 'msexcel',
        }

        fmt = file_extensions.get(type)
        if not fmt:
            self.logger.error(f"Got unsupported file type when downloading: {type}")
            return None
        
        # define the download URL parameters
        params = {
            'fmt': fmt,
            'auth': auth,
            'token': token
        }

        # make the GET request to download the file
        response = requests.get(TOKENS_DOWNLOAD_URL, params=params, allow_redirects=True)

        # check if the request was successful
        if response.status_code == 200:
            print_color(f"File content successfully downloaded", "INFO")
            return response.content
        else:
            self.logger.error(f"Failed to download content: {response.status_code} - {response.text}")

    def _inject_docx(self, filepath, honeytoken):
        temp_dir = filepath + "_tmp"

        with zipfile.ZipFile(filepath, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        doc_xml_path = os.path.join(temp_dir, "word", "document.xml")
        ET.register_namespace('w', "http://schemas.openxmlformats.org/wordprocessingml/2006/main")
        tree = ET.parse(doc_xml_path)
        root = tree.getroot()
        body = root.find("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}body")
        children = list(body)

        if children and children[-1].tag.endswith("sectPr"):
            sectPr = children[-1]
            body.remove(sectPr)
        else:
            sectPr = None

        def make_paragraph(text):
            ns = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
            p = ET.Element(f"{{{ns}}}p")
            r = ET.SubElement(p, f"{{{ns}}}r")
            t = ET.SubElement(r, f"{{{ns}}}t")
            t.text = saxutils.escape(text)
            return p

        lines = self._generate_fake_content_from_llm(honeytoken, "docx")
        for line in lines:
            body.append(make_paragraph(line))

        if sectPr is not None:
            body.append(sectPr)

        tree.write(doc_xml_path, encoding="UTF-8", xml_declaration=True)

        tmp_output = filepath + ".tmp"
        with zipfile.ZipFile(tmp_output, 'w', zipfile.ZIP_DEFLATED) as docx_zip:
            for folder, _, files in os.walk(temp_dir):
                for file in files:
                    full_path = os.path.join(folder, file)
                    rel_path = os.path.relpath(full_path, temp_dir)
                    docx_zip.write(full_path, rel_path)

        shutil.move(tmp_output, filepath)
        shutil.rmtree(temp_dir)

        self.logger.debug(f"Injected the generated data {lines} into .docx honeytoken with the hashed filename {filepath}")


    def _inject_xlsx(self, filepath, honeytoken):
        temp_dir = filepath + "_tmp"

        with zipfile.ZipFile(filepath, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        sheet_xml = os.path.join(temp_dir, "xl", "worksheets", "sheet1.xml")
        tree = ET.parse(sheet_xml)
        root = tree.getroot()
        ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        ET.register_namespace('', ns["x"])

        sheet_data = root.find("x:sheetData", ns)
        dimension = root.find("x:dimension", ns)

        def col_letter(n):
            result = ''
            while n > 0:
                n, remainder = divmod(n - 1, 26)
                result = chr(65 + remainder) + result
            return result

        def make_row(row_idx, values):
            row = ET.Element(f"{{{ns['x']}}}row", attrib={"r": str(row_idx), "spans": f"1:{len(values)}"})
            for col_idx, val in enumerate(values):
                col = col_letter(col_idx + 1)
                cell = ET.SubElement(row, f"{{{ns['x']}}}c", attrib={"r": f"{col}{row_idx}", "t": "inlineStr"})
                is_elem = ET.SubElement(cell, f"{{{ns['x']}}}is")
                t_elem = ET.SubElement(is_elem, f"{{{ns['x']}}}t")
                t_elem.text = saxutils.escape(val)
            return row

        existing_rows = sheet_data.findall("x:row", ns)
        start_row = max((int(row.attrib.get("r", "0")) for row in existing_rows), default=0) + 1

        rows = self._generate_fake_content_from_llm(honeytoken, "xlsx")

        for i, line in enumerate(rows):
            values = [v.strip() for v in line.split(",") if v.strip()]
            sheet_data.append(make_row(start_row + i, values))

        last_row = start_row + len(rows) - 1
        last_col = col_letter(max(len(r.split(",")) for r in rows)) if rows else "A"
        if dimension is not None:
            dimension.set("ref", f"A1:{last_col}{last_row}")

        tree.write(sheet_xml, encoding="UTF-8", xml_declaration=True, method="xml")

        tmp_output = filepath + ".tmp"
        with zipfile.ZipFile(tmp_output, 'w', zipfile.ZIP_DEFLATED) as xlsx_zip:
            for folder, _, files in os.walk(temp_dir):
                for file in files:
                    full_path = os.path.join(folder, file)
                    rel_path = os.path.relpath(full_path, temp_dir)
                    xlsx_zip.write(full_path, rel_path)

        shutil.move(tmp_output, filepath)
        shutil.rmtree(temp_dir)

        self.logger.debug(f"Injected the generated data {rows} into .xlsx honeytoken with the hashed filename {filepath}")


    def _generate_fake_content_from_llm(self, honeytoken: str, filetype: str):
        """
        Generate realistic fake content for XML injection based on honeytoken filename.
        Uses prompts from config with {honeytoken} placeholder.
        Returns a list of clean lines.
        """
        options = [
            "realistic as the CEO that you are.",
            "boring..",
            "juicy wow!",
            "tempting for a thief!!",
            "simple and clean.",
            "as bland as an IT compliance report.",
            "dripping with secrets.",
            "convincingly corporate.",
            "leaking subtle danger.",
            "quietly explosive.",
            "like it fell off the back of a server.",
            "barely legal.",
            "flashy enough to get flagged by an intern.",
            "low-key shady.",
            "tempting like a forbidden folder.",
            "desperate for a double-click.",
            "one wrong click away from disaster.",
            "suspiciously tidy.",
            "hacked-together brilliance.",
            "just corporate enough to be overlooked.",
            "too good to be left in plain sight.",
            "enticing to someone who knows what to look for.",
            "so juicy it should be encrypted.",
            "hidden in plain sight.",
            "ready to blow the whistle.",
            "like evidence waiting to be found.",
            "seductive in a spreadsheet kind of way.",
            "a little too confidential.",
            "like it belongs in a courtroom.",
            "mistakenly public.",
            "so official it hurts.",
            "a digital honeytrap.",
            "cryptic but obvious.",
            "named for mischief.",
            "almost believable.",
            "from the dark side of the SharePoint.",
            "familiar but threatening.",
            "ticking with legal implications.",
            "worthy of blackmail.",
            "bait for the bold.",
            "quietly screaming 'look at me'.",
            "the filename equivalent of clickbait.",
            "designed to cause a breach report.",
            "innocent enough to be deadly.",
            "sweet as social engineering bait.",
            "just boring enough to be ignored — or not.",
            "suspenseful like a spy novel title.",
            "like a mistake someone made at 2 AM.",
            "a juicy secret disguised as compliance."
        ]
        dynamic = random.choice(options)
        if filetype == "docx":
            prompt = (
                SnareConfig.get("HONEYTOKEN", "PROMPT-DOCX")
                .replace("{honeytoken}", honeytoken)
                .replace("{dynamic}", dynamic)
            )
        elif filetype == "xlsx":
            prompt = (
                SnareConfig.get("HONEYTOKEN", "PROMPT-XLSX")
                .replace("{honeytoken}", honeytoken)
                .replace("{dynamic}", dynamic)
            )
        else:
            return []


        # Call the LLM
        if self.api_provider == "huggingface":
            text = self._call_huggingface_api(prompt)
        elif self.api_provider == "gemini":
            text = self._call_gemini_api(prompt)
        else:
            return []

        try:
            # Clean up response lines
            lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
            return lines
        except Exception as e:
            self.logger.error(f"Failed to process fake content from LLM: {e}")
            return []

    
