#import os
#import hashlib
#import json
#import shutil#

#from snare.utils.snare_helpers import print_color#

#class HoneytokensGenerator:
#    def __init__(self, 
#                 page_dir, 
#                 php_script_path=None):
#        self.page_dir = page_dir#

#        # Ensure the PHP script directory exists
#        if not os.path.exists(self.php_script_path):
#            os.makedirs(self.php_script_path)#

#    def generate_honeytokens(self, honeytokens):
#        # Your existing code to generate honeytokens
#        pass#

#    def generate_pdf_honeytoken(self):
#        """
#        Generates a pdf-file
#        """
#        file_name = "example.pdf"
#        hash_name = self.make_filename(file_name)
#        pdf_path = os.path.join(self.page_dir, hash_name)
#         
#        # If the robots.txt file does not exist, create it with default content.
#        if not os.path.exists(pdf_path):#
#
#
#
#

#            default_content = "User-agent: *\nDisallow:"  # You can adjust the content as needed.
#            with open(robots_path, "w") as f:
#                f.write(default_content)
#        
#            abs_url = "/robots.txt" 
#            self.meta[abs_url] = {
#                "hash": hash_name,
#                "content_type": "text/plain"
#            }#

#            # Save the updated meta dictionary to meta.json
#            meta_json_path = os.path.join(self.page_dir, "meta.json")
#            with open(meta_json_path, "w") as meta_file:
#                json.dump(self.meta, meta_file, indent=4)#

#        # Path to the honeytoken.php script
#        script_source_path = "/path/to/honeytoken.php"  # Update this path to the actual location of honeytoken.php#

#        # Destination path within the cloned pages
#        script_dest_path = os.path.join(self.php_script_path, "honeytoken.php")#

#        # Copy the honeytoken.php script to the destination path
#        shutil.copy(script_source_path, script_dest_path)
#        print_color(f"Honeytoken: PDF-token script placed at: {script_dest_path}")#
#

#    @staticmethod
#    def make_filename(file_name):
#        # Compute the MD5 hash of the content
#        m = hashlib.md5()  
#        m.update(file_name.encode("utf-8"))
#        hash_name = m.hexdigest()#

#        return hash_name