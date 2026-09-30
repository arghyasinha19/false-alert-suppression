"""
Single-command launcher for the False Alert Suppression Dashboard.
Starts both the FastAPI Backend (port 8004) and Vite React Frontend (port 5173).
Press Ctrl+C to stop both services gracefully.
"""
import os
import sys
import subprocess
import time
import signal

project_root = os.path.dirname(os.path.abspath(__file__))
dashboard_dir = os.path.join(project_root, "dashboard")

def main():
    print("=" * 65)
    print("  False Alert Suppression Pipeline — Dashboard Launcher")
    print("=" * 65)

    backend_cmd = [
        sys.executable, "-m", "uvicorn", "dashboard.api:app",
        "--host", "127.0.0.1",
        "--port", "8004"
    ]
    
    # On Windows, npm is npm.cmd
    npm_bin = "npm.cmd" if sys.platform == "win32" else "npm"
    frontend_cmd = [npm_bin, "run", "dev"]

    print("\n[1/2] Starting FastAPI Backend on http://127.0.0.1:8004...")
    backend_proc = subprocess.Popen(
        backend_cmd,
        cwd=project_root,
        stdout=sys.stdout,
        stderr=sys.stderr
    )

    time.sleep(2)

    print("\n[2/2] Starting Vite Frontend on http://localhost:5173...")
    frontend_proc = subprocess.Popen(
        frontend_cmd,
        cwd=dashboard_dir,
        stdout=sys.stdout,
        stderr=sys.stderr
    )

    print("\n" + "=" * 65)
    print("  ✓ Services running:")
    print("    - Backend API: http://127.0.0.1:8004/api/alerts")
    print("    - Frontend UI: http://localhost:5173")
    print("  Press Ctrl+C to terminate both servers.")
    print("=" * 65 + "\n")

    def handle_exit(signum, frame):
        print("\nShutting down services...")
        try:
            backend_proc.terminate()
            frontend_proc.terminate()
        except Exception:
            pass
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    try:
        backend_proc.wait()
        frontend_proc.wait()
    except KeyboardInterrupt:
        handle_exit(None, None)

if __name__ == "__main__":
    main()
