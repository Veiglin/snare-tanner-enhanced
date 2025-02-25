import os
import hashlib
import json

from snare.utils.snare_helpers import print_color

class BreadcrumbsGenerator:
    def __init__(self, page_dir, meta, breadcrumb='robots'):
        """
        Initializes the breadcrumbs generator.
        
        :param page_dir: The directory where cloned pages are stored.
        :param meta: The meta dictionary (parsed from meta.json).
        :param breadcrumb: The type of breadcrumb to generate. Currently supports 'robots' only.
        """
        self.page_dir = page_dir
        self.meta = meta
        self.breadcrumb = breadcrumb

    def generate_breadcrumbs(self):
        """
        Generates breadcrumbs for the given type. For now, it creates/updates a robots.txt file.
        The file's MD5 hash is computed and added to the meta dictionary.
        """
        if self.breadcrumb in ['robots']:
            # Use the _make_filename_for_robots method to compute the MD5 hash.
            file_name = "robots.txt"
            hash_name = self.make_filename(file_name)

            robots_path = os.path.join(self.page_dir, hash_name)
            # If the robots.txt file does not exist, create it with default content.
            if not os.path.exists(robots_path):
                default_content = "User-agent: *\nDisallow:"  # You can adjust the content as needed.
                with open(robots_path, "w") as f:
                    f.write(default_content)
            
            abs_url = "/robots.txt" 
            self.meta[abs_url] = {
                "hash": hash_name,
                "content_type": "text/plain"
            }

            # Save the updated meta dictionary to meta.json
            meta_json_path = os.path.join(self.page_dir, "meta.json")
            with open(meta_json_path, "w") as meta_file:
                json.dump(self.meta, meta_file, indent=4)

            print_color("Breadcrumbing: Added robots.txt as breadcrumb with hash '{}'".format(hash_name))

        if self.breadcrumb in ['404_page']:

            # find the 404 page hash in the meta dictionary
            for key, val in self.meta.items():
                if "404" in key:
                    abs_url = key
                    hash_name = val["hash"]
                    break
            
            # go to the hash file name and change the content of the html file
            html_path = os.path.join(self.page_dir, hash_name)
            with open(html_path, "r") as f:
                html_content = f.read()
                # change the content of the 404 page as needed by adding a message
                msg = "<p>Try accessing test, test, test for more information.</p>"
                html_content = html_content.replace("</body>", msg + "</body>")

            # save the new content in the hash file
            with open(html_path, "w") as f:
                f.write(html_content)

            print_color("Breacrumbing: Updated 404 page with message '{}'".format(msg))

        #else:
        #    print_color("Breadcrumbing: Breadcrumb type '{}' is not supported yet.".format(self.breadcrumb), "WARNING")

    @staticmethod
    def make_filename(file_name):
        # Compute the MD5 hash of the content
        m = hashlib.md5()  
        m.update(file_name.encode("utf-8"))
        hash_name = m.hexdigest()

        return hash_name