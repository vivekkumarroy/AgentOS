import requests
import json
import time
import subprocess
import os
import signal

def run_verification():
    print("="*50)
    print("PHASE 7 MANUAL VERIFICATION SCRIPT")
    print("="*50)

    # 1. Start Server
    print("Starting AgentOS server...")
    process = subprocess.Popen(
        ["python", "-m", "uvicorn", "src.api:app", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=os.path.abspath(os.path.dirname(__file__))
    )
    print("Waiting for server to start...")
    max_retries = 15
    for i in range(max_retries):
        try:
            requests.get("http://127.0.0.1:8000/health")
            break
        except requests.exceptions.ConnectionError:
            time.sleep(1)
    else:
        print("❌ Server failed to start within 15 seconds")
        process.terminate()
        return

    try:
        # 2. Check /health
        print("\nChecking /health...")
        health_resp = requests.get("http://127.0.0.1:8000/health")
        print(f"Status Code: {health_resp.status_code}")
        print(f"Response: {health_resp.json()}")
        if health_resp.json() != {"status": "ok"}:
            print("[FAIL] /health returned unexpected format")
        else:
            print("[PASS] /health passed")

        # 3. Check /ready
        print("\nChecking /ready...")
        ready_resp = requests.get("http://127.0.0.1:8000/ready")
        print(f"Status Code: {ready_resp.status_code}")
        print(f"Response: {ready_resp.json()}")
        if ready_resp.json() != {"status": "ready"}:
            print("[FAIL] /ready returned unexpected format")
        else:
            print("[PASS] /ready passed")

        # 4. Check Structured Error Handling
        print("\nChecking Structured Error Handling (Invalid Payload)...")
        error_resp = requests.post("http://127.0.0.1:8000/tools/execute", json={"invalid": "data"})
        print(f"Status Code: {error_resp.status_code}")
        print(f"Response: {error_resp.json()}")
        if error_resp.status_code == 422:
            print("[PASS] Validation error passed")
        else:
            print("[FAIL] Validation error failed")

    finally:
        print("\nStopping server...")
        if os.name == 'nt':
            subprocess.call(['taskkill', '/F', '/T', '/PID', str(process.pid)])
        else:
            process.terminate()

if __name__ == "__main__":
    run_verification()
