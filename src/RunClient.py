from src.Peer import Peer

ROOT_IP = 'localhost'
ROOT_PORT = 5050
ROOT_ADDRESS = (ROOT_IP, ROOT_PORT)

if __name__ == "__main__":
    client = Peer("localhost", 6060, is_root=False,
                  root_address=ROOT_ADDRESS)
