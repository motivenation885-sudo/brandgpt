"""
serve.py — starts Flask webhook (port 5001) + Streamlit UI (port 5000).

Architecture:
  - Streamlit 1.57 uses Starlette/Uvicorn — Tornado handler mounting is not possible.
  - Flask webhook runs on port 5001 in a daemon thread.
  - Streamlit runs on port 5000 via subprocess (main process).
  - Replit exposes BOTH ports publicly with separate URLs.

Twilio webhook URL → https://5001-<your-replit-dev-domain>/webhook
Streamlit UI      → https://<your-replit-dev-domain>  (port 5000)

Run: python serve.py
"""

import subprocess
import sys
import threading
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
log = logging.getLogger("halo.serve")


def run_flask():
    from webhook import app
    log.info("Flask webhook starting on 0.0.0.0:5001 ...")
    app.run(host="0.0.0.0", port=5001, debug=False, use_reloader=False)


def main():
    # Start Flask webhook in a background daemon thread
    t = threading.Thread(target=run_flask, daemon=True, name="flask-webhook")
    t.start()

    # Brief pause so Flask logs print before Streamlit floods stdout
    time.sleep(1)

    log.info("Streamlit UI starting on 0.0.0.0:5000 ...")
    subprocess.run(
        [
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port=5000",
            "--server.address=0.0.0.0",
            "--server.headless=true",
            "--server.enableCORS=false",
            "--server.enableXsrfProtection=false",
        ],
        check=False,
    )


if __name__ == "__main__":
    main()
