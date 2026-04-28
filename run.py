# run.py - Single file to launch everything
import subprocess
import time
import sys
import os
import signal

def main():
    print("Starting DocuMind AI...")
    
    # Start FastAPI backend
    print("Starting backend server...")
    backend = subprocess.Popen([sys.executable, "main.py"])
    
    # Wait for backend to start
    time.sleep(3)
    
    # Start Streamlit frontend
    print("Starting frontend application...")
    frontend = subprocess.Popen(["streamlit", "run", "streamlit_app.py"])
    
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        print("\nShutting down...")
        backend.terminate()
        frontend.terminate()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        frontend.wait()
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()