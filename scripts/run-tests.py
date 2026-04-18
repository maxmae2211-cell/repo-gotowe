#!/usr/bin/env python
# Test Runner - Alternative to PowerShell
# -*- coding: utf-8 -*-

import subprocess
import os
import sys
import time
from pathlib import Path
import threading

def main():
    # Setup paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Use virtualenv Python
    venv_python = project_root / ".venv-1" / "Scripts" / "python.exe"
    if venv_python.exists():
        sys.executable = str(venv_python)
    print(f"Using Python: {sys.executable}")
    
    test_dir = project_root / "tests" / "api"
    
    print("=" * 50)
    print("Taurus Load Testing Suite")
    print("=" * 50)
    print(f"Project: {project_root}")
    print()
    
    # Kill any existing processes on port 8000
    import subprocess
    try:
        result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if ':8000' in line and 'LISTENING' in line:
                pid = line.split()[-1]
                subprocess.run(["taskkill", "/PID", pid, "/F"], capture_output=True)
    except:
        pass
    
    # Start mock server
    print("Starting mock API server...")
    server_process = subprocess.Popen([sys.executable, str(script_dir / "mock-api-server.py")])
    time.sleep(15)
    
    # Verify server
    try:
        import urllib.request
        urllib.request.urlopen("http://localhost:8000/get", timeout=10)
        print("[OK] Mock API server running on http://localhost:8000\n")
    except Exception as e:
        print(f"[ERROR] Failed to start server: {e}")
        return 1
    
    # Find tests
    test_files = sorted(test_dir.glob("*.yml"))
    if not test_files:
        print(f"No test files found in {test_dir}")
        return 1
    
    print(f"Found {len(test_files)} tests\n")
    
    # Run tests
    passed = 0
    failed = 0
    
    for test_file in test_files:
        print("-" * 50)
        print(f"Running: {test_file.stem}")
        print("-" * 50)
        
        result = subprocess.run(
            [sys.executable, "-m", "bzt", str(test_file)],
            capture_output=False
        )
        
        if result.returncode == 0:
            print(f"[OK] PASSED: {test_file.stem}\n")
            passed += 1
        else:
            print(f"[ERROR] FAILED: {test_file.stem}\n")
            failed += 1
    
    # Stop server
    print("Stopping mock API server...")
    server_process.terminate()
    try:
        server_process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        server_process.kill()
    
    # Summary
    print("=" * 50)
    print("Test Summary")
    print("=" * 50)
    print(f"Total Tests: {len(test_files)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print("=" * 50)
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
