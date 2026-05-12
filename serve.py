"""
serve.py — starts Flask webhook (port 5001) + Streamlit UI (port 5000).
Run: python serve.py
"""

import subprocess
import sys
import threading
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("halo.serve")


def run_flask():
    """Flask webhook on port 5001 in a background daemon thread."""
    from webhook import app
    log.info("Starting Flask webhook on port 5001 ...")
    app.run(host="0.0.0.0", port=5001, debug=False, use_reloader=False)


def main():
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()
    log.info("Flask webhook thread started on port 5001.")

    log.info("Starting Streamlit on port 5000 ...")
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.port=5000",
        "--server.address=0.0.0.0",
        "--server.headless=true",
        "--server.enableCORS=false",
        "--server.enableXsrfProtection=false",
    ])


if __name__ == "__main__":
    main()
