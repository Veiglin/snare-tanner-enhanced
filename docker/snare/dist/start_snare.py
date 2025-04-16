#!/usr/bin/env python3
import subprocess
import random
import os

dirs = [
    "smartgadgetstore1",
    "smartgadgetstore2",
    "smartgadgetstore3",
    "smartgadgetstore4"
]

selected_dir = random.choice(dirs)

cmd = [
    "snare",
    "--tanner", "tanner",
    "--debug", "true",
    "--auto-update", "false",
    "--host-ip", "0.0.0.0",
    "--port", "443",
    "--page-dir", selected_dir,
    "--breadcrumbs", "robots", "robots", "404_page", "html_comments"
]

subprocess.run(cmd)

