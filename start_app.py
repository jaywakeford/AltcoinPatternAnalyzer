import os
import sys
import time
import socket
from subprocess import Popen

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return False
        except:
            return True

def find_free_port(start_port=8520, end_port=8540):
    for port in range(start_port, end_port):
        if not is_port_in_use(port):
            return port
    return None

def main():
    # Find a free port
    port = find_free_port()
    if not port:
        print("No free ports found between 8520 and 8540")
        return
    
    print(f"Starting Streamlit on port {port}")
    
    # Use the known path to streamlit
    streamlit_path = r"C:\Users\jaywa\AppData\Roaming\Python\Python312\Scripts\streamlit.exe"
    
    if not os.path.exists(streamlit_path):
        print(f"Error: Streamlit not found at {streamlit_path}")
        print("Please make sure Streamlit is installed correctly.")
        return
    
    # Start Streamlit
    cmd = [
        streamlit_path,
        "run",
        "--server.port", str(port),
        "--server.address", "localhost",
        "app.py"
    ]
    
    try:
        process = Popen(cmd)
        print(f"Application started! Visit http://localhost:{port}")
        print("Press Ctrl+C to stop the server...")
        process.wait()
    except KeyboardInterrupt:
        process.terminate()
        print("\nServer stopped.")
    except Exception as e:
        print(f"Error starting Streamlit: {e}")

if __name__ == "__main__":
    main()
