from src.Peer import Peer

ROOT_IP = "127.0.0.1"
ROOT_PORT = 5050
ROOT_ADDRESS = (ROOT_IP, ROOT_PORT)

if __name__ == "__main__":
    server = Peer(ROOT_IP, ROOT_PORT, is_root=True)
    server.run()
