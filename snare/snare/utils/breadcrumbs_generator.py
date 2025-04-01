import os
import hashlib
import json
import random


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
                self.generate_html_comments_breadcrumb()
            else:
                print_color("Breadcrumb type '{}' is not supported yet.".format(breadcrumb), "WARNING")

    def generate_robots_breadcrumb(self):
        """
        Generates or refreshes robots.txt with realistic bait paths.
        """
        file_name = "robots.txt"
        hash_name = self.make_filename(file_name)
        robots_path = os.path.join(self.page_dir, hash_name)

        # Check if /robots.txt is in meta.json — if not, add it
        abs_url = "/robots.txt"
        if abs_url not in self.meta:
            self.meta[abs_url] = {
                "hash": hash_name,
                "content_type": "text/plain"
            }
        else:
            # Already exists — clear old content
            with open(robots_path, "w") as f:
                f.write("")

        # Load bait from honeytokens
        honeytoken_path = "/opt/snare/honeytokens/Honeytokens.txt"
        bait_lines = []
        bait_sample = []
        if os.path.exists(honeytoken_path):
            with open(honeytoken_path, "r") as f:
                tokens = [line.strip() for line in f if line.strip()]
                if tokens:
                    bait_sample = random.sample(tokens, min(len(tokens), 3))
                    bait_lines = [f"Disallow: /{token}" for token in bait_sample]

        lines = [
            "User-agent: *",
            ""
        ] + bait_lines + [
            "Disallow: /private/",
            "Disallow: /admin/",
            "",
            "Sitemap: https://smartgadgetstore.live/sitemap.xml"
        ]

        # Write the new content
        with open(robots_path, "w") as f:
            f.write("\n".join(lines))

        # Save meta.json (in case it was just added)
        meta_json_path = os.path.join(self.page_dir, "meta.json")
        with open(meta_json_path, "w") as meta_file:
            json.dump(self.meta, meta_file, indent=4)

        if bait_sample:
            print_color(f"Breadcrumbing: Refreshed robots.txt with bait: {bait_sample}", "SUCCESS")
        else:
            print_color("Breadcrumbing: Refreshed robots.txt (no honeytokens found)", "SUCCESS")



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

    def generate_html_comments_breadcrumb(self):
        """
        Generates a breadcrumb for the HTML comments page.
        
        :param html_comments_abs_url: The absolute URL of the HTML comments page.
        """
        # find the hash of the html comments page in the meta dictionary
        for key, val in self.meta.items():
            if self.html_comments_abs_url in key:
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

        print_color("Breadcrumbing: Updated HTML page '{}' with the comment '{}' for breadcrumbing".format(self.html_comments_abs_url, msg))

    @staticmethod
    def make_filename(file_name):
        # Compute the MD5 hash of the content
        m = hashlib.md5()  
        m.update(file_name.encode("utf-8"))
        hash_name = m.hexdigest()

        return hash_name