"""
serve.py — mounts /webhook inside Streamlit's own Starlette/Uvicorn server.

How it works:
  Streamlit 1.57 uses Starlette + Uvicorn (NOT Tornado).
  We monkeypatch `create_streamlit_routes` before bootstrap starts.
  Our webhook routes are prepended to Streamlit's route list so they
  are matched FIRST — before Streamlit's SPA catch-all route.
  Everything runs on port 5000. No Flask. No second server.

Twilio webhook URL → https://<your-replit-dev-domain>/webhook
Run: python serve.py
"""

import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
log = logging.getLogger("halo.serve")

# ── Monkeypatch create_streamlit_routes BEFORE importing bootstrap ────────────
# Starlette processes routes in order. Prepending here means /webhook is
# checked before Streamlit's catch-all SPA route gets a chance to intercept.

log.info("Patching create_streamlit_routes to mount /webhook ...")

import streamlit.web.server.starlette.starlette_app as _st_mod

_orig_create_routes = _st_mod.create_streamlit_routes


def _patched_create_routes(runtime):
    from webhook import WEBHOOK_ROUTES
    original_routes = _orig_create_routes(runtime)
    combined = WEBHOOK_ROUTES + list(original_routes)
    log.info(
        "SUCCESS: %d webhook route(s) prepended. Total Starlette routes: %d",
        len(WEBHOOK_ROUTES),
        len(combined),
    )
    return combined


_st_mod.create_streamlit_routes = _patched_create_routes
log.info("Monkeypatch applied to create_streamlit_routes.")

# ── Start Streamlit in-process (patch must be in the same process) ────────────
log.info("Starting Streamlit on port 5000 ...")

sys.argv = [
    "streamlit", "run", "app.py",
    "--server.port=5000",
    "--server.address=0.0.0.0",
    "--server.headless=true",
    "--server.enableCORS=false",
    "--server.enableXsrfProtection=false",
]

from streamlit.web import bootstrap
# bootstrap.run(main_script_path, is_hello: bool, args, flag_options)
bootstrap.run("app.py", False, [], {})
