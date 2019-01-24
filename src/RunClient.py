from RunRoot import ROOT_ADDRESS
from src.Peer import Peer

if __name__ == "__main__":
    client = Peer("127.0.0.1", 9018, is_root=False,
                  root_address=ROOT_ADDRESS)
    client.run()
