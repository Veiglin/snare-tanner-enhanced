import os
import hashlib
import logging
import json

from snare.utils.snare_helpers import check_privileges, print_color

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
            # Determine the path for robots.txt in the cloned pages directory.
            robots_path = os.path.join(self.page_dir, "robots")
            
            # If the robots.txt file does not exist, create it with default content.
            if not os.path.exists(robots_path):
                default_content = "User-agent: *\nDisallow:"  # You can adjust the content as needed.
                with open(robots_path, "w") as f:
                    f.write(default_content)
            
            # Use the _make_filename_for_robots method to compute the MD5 hash.
            #file_name, hash_name = self._make_filename_for_robots()
            file_name = "/robots.txt"  # Placeholder for the file name.
            hash_name = 'robots'  # Placeholder for the hash value.
            
            # Update the meta dictionary with the robots.txt entry.
            self.meta[file_name] = {
                "hash": hash_name,
                "content_type": "text/plain"
            }

            # Save the updated meta dictionary to meta.json
            meta_json_path = os.path.join(self.page_dir, "meta.json")
            with open(meta_json_path, "w") as meta_file:
                json.dump(self.meta, meta_file, indent=4)

            print_color("Added robots.txt as breadcrumb with hash '{}'".format(hash_name))

        else:
            print_color("Breadcrumb type '{}' is not supported yet.".format(self.breadcrumb), "WARNING")


    def _make_filename(self, path):
        # Compute the MD5 hash of the content
        with open(path, "r") as f:
            content = f.read()
        m = hashlib.md5()  
        m.update(content.encode("utf-8"))
        hash_name = m.hexdigest()

        return hash_name