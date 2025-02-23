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
            
            # If the robots.txt file does not exist, create it with default content.
            if not os.path.exists(robots_path):
                default_content = "User-agent: *\nDisallow:"  # You can adjust the content as needed.
                with open(robots_path, "w") as f:
                    f.write(default_content)
            
            # Compute the MD5 hash of the robots.txt file.
            md5_hash = self._compute_md5(robots_path)
            
            # Update the meta dictionary with an entry for robots.txt.
            # The key is formatted to match the style in meta.json (e.g., "/index.html").
            self.meta["/robots.txt"] = {
                "hash": md5_hash,
                "content_type": "text/plain"
            }
            print("Breadcrumbs: Added robots.txt with hash {}".format(md5_hash))
        else:
            print("Breadcrumb type '{}' is not supported yet.".format(self.breadcrumb))

    def _compute_md5(self, file_path):
        """
        Computes and returns the MD5 hash of the specified file.
        """
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
