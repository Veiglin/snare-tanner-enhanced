import os
import hashlib
import json

from snare.utils.snare_helpers import print_color

class BreadcrumbsGenerator:
    def __init__(self, page_dir, meta, breadcrumb, html_comments_abs_url = None):
        """
        Initializes the breadcrumbs generator.
        
        :param page_dir: The directory where cloned pages are stored.
        :param meta: The meta dictionary (parsed from meta.json).
        :param breadcrumb: The type of breadcrumb to generate.
        :param html_comments_abs_url: The absolute URL of the HTML comments page.
        """
        self.page_dir = page_dir
        self.meta = meta
        self.breadcrumb = breadcrumb
        self.html_comments_abs_url = html_comments_abs_url
    
    def generate_breadcrumbs(self):
        """
        Generates breadcrumbs for the given types.
        """
        for breadcrumb in self.breadcrumb:
            if breadcrumb == 'robots':
                self.generate_robots_breadcrumb()
            elif breadcrumb == '404_page':
                self.generate_404_breadcrumb()
            elif breadcrumb == 'html_comments' and self.html_comments_abs_url:
                self.generate_html_comments_breadcrumb(self.html_comments_abs_url)
            else:
                print_color("Breadcrumb type '{}' is not supported yet.".format(breadcrumb), "WARNING")

    def generate_robots_breadcrumb(self):
        """
        Generates a robots.txt breadcrumb.
        """
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
        else:
            print_color("Breadcrumbing: robots.txt already exists.")

    def generate_404_breadcrumb(self):
        """
        Generates a 404 page breadcrumb.
        """
        # find the 404 page hash in the meta dictionary
        for key, val in self.meta.items():
            if "404" in key:
                hash_name = val["hash"]
                break
            
        # go to the hash file name and change the content of the html file
        html_path = os.path.join(self.page_dir, hash_name)
        with open(html_path, "r") as f:
            html_content = f.read()
            # check if the 404 page already has a message
            if "Try accessing" in html_content:
                print_color("Breadcrumbing: 404 page already has a custom message.")
                return None
            # change the content of the 404 page as needed by adding a message
            msg = "<p>Try accessing test, test, test for more information.</p>"
            html_content = html_content.replace("</body>", msg + "</body>")

        # save the new content in the hash file
        with open(html_path, "w") as f:
            f.write(html_content)

        print_color("Breacrumbing: Updated 404 page with message '{}'".format(msg))

    def generate_html_comments_breadcrumb(self, html_comments_abs_url):
        """
        Generates a breadcrumb for the HTML comments page.
        
        :param html_comments_abs_url: The absolute URL of the HTML comments page.
        """
        # find the hash of the html comments page in the meta dictionary
        for key, val in self.meta.items():
            if html_comments_abs_url in key:
                hash_name = val["hash"]
                break
        
        # go to the hash file name and change the content of the html file
        html_path = os.path.join(self.page_dir, hash_name)
        with open(html_path, "r") as f:
            html_content = f.read()
            # check if the html breadcrumb comments already exists
            if "This is a breadcrumb comment" in html_content:
                print_color("Breadcrumbing: HTML comments page already has a custom message.")
                return None
            # change the content of the html adding a comments as breadcrumb
            msg = "<!-- This is a breadcrumb comment -->"
            html_content = html_content.replace("</body>", msg + "</body>")

        # save the new content in the hash file
        with open(html_path, "w") as f:
            f.write(html_content)

        print_color("Breacrumbing: Updated HTML page  '{}' with the comment '{}' for breadcrumbing".format(html_comments_abs_url, msg))

    @staticmethod
    def make_filename(file_name):
        # Compute the MD5 hash of the content
        m = hashlib.md5()  
        m.update(file_name.encode("utf-8"))
        hash_name = m.hexdigest()

        return hash_name