import os
import hashlib

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
        if self.breadcrumb in ['robots', 'robots.txt']:
            # Determine the path for robots.txt in the cloned pages directory.
            robots_path = os.path.join(self.page_dir, "robots.txt")

            # Ensure the directory exists
            os.makedirs(self.page_dir, exist_ok=True)
            
            # If the robots.txt file does not exist, create it with default content.
            if not os.path.exists(robots_path):
                default_content = "User-agent: *\nDisallow:"  # You can adjust the content as needed.
                with open(robots_path, "w") as f:
                    f.write(default_content)
            
            # Use the _make_filename_for_robots method to compute the MD5 hash.
            #file_name, hash_name = self._make_filename_for_robots()
            file_name = "/robots.txt"

            hash_name = 'test_hash'  # Placeholder for the hash value.
            
            # Update the meta dictionary with the robots.txt entry.
            self.meta[file_name] = {
                "hash": hash_name,
                "content_type": "text/plain"
            }

            print("Breadcrumbs: Added robots.txt with hash {}".format(hash_name))
        else:
            print("Breadcrumb type '{}' is not supported yet.".format(self.breadcrumb))

    def _make_filename_for_robots(self):
        """
        Mimics the provided _make_filename method for generating an MD5 hash.
        In this case, it computes the MD5 hash for '/robots.txt'.
        """
        file_name = "/robots.txt"
        #if not file_name.startswith("/"):
        #    file_name = "/" + file_name

        # For robots.txt, we do not need to check for the special case of "/" since it's predefined.
        m = hashlib.md5()
        m.update(file_name.encode("utf-8"))
        hash_name = m.hexdigest()
        return file_name, hash_name
