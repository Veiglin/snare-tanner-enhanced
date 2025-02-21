
from ..cloner import _make_filename

# adding breadcrumbs into the cloned page
class BreadcrumbsGenerator:
    def __init__(self, page_dir, meta, breadcrumb = 'robots') -> None:
        self.page_dir = page_dir
        self.meta = meta
        self.breadcrumb = breadcrumb
    
    def generate_breadcrumbs(self):
        if self.breadcrumb == 'robots':
            # add robots.txt to the metadata first and then add robots.txt 
            robots = {
                "hash": "robots.txt",
                "headers": [
                    {"Content-Type": "text/plain"},
                ],
            }
            self.meta["robots.txt"] = robots
            breadcrumbs.append("robots.txt")


