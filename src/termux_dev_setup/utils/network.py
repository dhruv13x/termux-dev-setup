import socket

def is_port_open(host="127.0.0.1", port=5432, timeout=0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False
