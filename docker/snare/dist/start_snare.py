#!/usr/bin/env python3
import subprocess
import random
import time
import requests

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
    "--page-dir", selected_dir
]


def wait_for_tanner(url="http://tanner:8090/version", retries=10):
    for i in range(retries):
        try:
            r = requests.get(url, timeout=2)
            if r.ok:
                return
        except Exception:
            time.sleep(2)
    raise RuntimeError("Tanner service did not start in time.")

wait_for_tanner()
# then start snare


subprocess.run(cmd)

