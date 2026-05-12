"""
serve.py — starts Streamlit and mounts webhook handlers on same port.
Run: python serve.py  (Replit's run command)
"""

import asyncio
import sys
import threading

import streamlit.web.bootstrap as bootstrap
import tornado.ioloop
import tornado.web

from webhook import HANDLERS


def patch_streamlit_server():
    """Wait for Streamlit's Tornado app to start, then add webhook routes."""
    import time
    from streamlit.web.server.server import Server

    for _ in range(60):
        try:
            server = Server.get_current()
            app = server._runtime._session_mgr  # noqa
            break
        except Exception:
            pass
        try:
            # Streamlit 1.x
            server = Server.get_current()
            break
        except Exception:
            time.sleep(0.5)
    else:
        print("Could not find Streamlit server to patch.")
        return

    try:
        # Access the underlying Tornado app and add our routes
        tornado_app = server._runtime._server._app  # noqa
        tornado_app.add_handlers(".*", HANDLERS)
        print("Webhook handlers mounted successfully.")
    except Exception as e:
        print(f"Handler mount failed: {e}")


def main():
    t = threading.Thread(target=patch_streamlit_server, daemon=True)
    t.start()

    sys.argv = [
        "streamlit",
        "run",
        "app.py",
        "--server.port=5000",
        "--server.address=0.0.0.0",
    ]
    bootstrap.run("app.py", "", [], {})


if __name__ == "__main__":
    main()
