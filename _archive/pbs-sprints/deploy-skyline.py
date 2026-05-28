#!/usr/bin/env python3
"""
deploy-skyline.py
Injects Austin skyline header CSS into PBS WordPress site
via WP REST API (wp/v2/settings → custom_css)
Usage: python3 deploy-skyline.py <app_password>
"""

import sys
import requests
import base64
import json

SITE = "https://newsite.psibetasigma1914.org"
USER = "s2tdesignadmin"

def deploy(app_password):
    auth = base64.b64encode(f"{USER}:{app_password}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json"
    }

    # Read the CSS
    with open(".agents/projects/s2tdesigns/clients/pbs/skyline-header-css.css") as f:
        new_css = f.read()

    # Get existing custom CSS first
    r = requests.get(f"{SITE}/wp-json/wp/v2/global-styles/themes/kadence", headers=headers)
    print("Theme styles status:", r.status_code)

    # Try via wp_css endpoint (custom CSS in Customizer)
    r = requests.get(f"{SITE}/wp-json/wp/v2/settings", headers=headers)
    if r.status_code == 200:
        settings = r.json()
        existing_css = settings.get("custom_css", "") or ""
        print(f"Existing CSS length: {len(existing_css)} chars")

        # Remove old skyline block if present, then append
        marker_start = "/* PBS Austin Sigmas — Skyline Header CSS */"
        if marker_start in existing_css:
            # Replace existing block
            import re
            existing_css = re.sub(
                r'/\* PBS Austin Sigmas.*?(?=\/\*|$)',
                '',
                existing_css,
                flags=re.DOTALL
            ).strip()

        merged_css = existing_css + "\n\n" + new_css if existing_css else new_css

        # Push updated CSS
        update = requests.post(
            f"{SITE}/wp-json/wp/v2/settings",
            headers=headers,
            json={"custom_css": merged_css}
        )
        if update.status_code == 200:
            print("✅ Skyline CSS deployed successfully via wp/v2/settings")
            return True
        else:
            print(f"❌ Settings update failed: {update.status_code} — {update.text[:300]}")
    else:
        print(f"❌ Auth failed or settings not accessible: {r.status_code} — {r.text[:300]}")
    return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 deploy-skyline.py <app_password>")
        sys.exit(1)
    deploy(sys.argv[1])
