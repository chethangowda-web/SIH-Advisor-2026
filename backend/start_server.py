"""
start_server.py
Self-healing launcher. Runs the API and automatically restarts it if it ever
crashes, so the backend is always available. Usage:
    python start_server.py
"""

import os
import time
import traceback

import config


def main() -> None:
    import uvicorn

    port = int(os.getenv("PORT", config.PORT))
    print(f"[supervisor] SIH AI Advisor on http://0.0.0.0:{port} (auto-restarts on crash)")
    while True:
        try:
            uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")
            print("[supervisor] server exited cleanly.")
            break
        except KeyboardInterrupt:
            print("[supervisor] stopped by user.")
            break
        except SystemExit:
            break
        except Exception:
            traceback.print_exc()
            print("[supervisor] server crashed; restarting in 3s...")
            time.sleep(3)


if __name__ == "__main__":
    main()