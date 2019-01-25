import threading

import PySimpleGUI as sg

from src.Peer import Peer

ROOT_IP = "127.0.0.1"
ROOT_PORT = 5050
ROOT_ADDRESS = (ROOT_IP, ROOT_PORT)


class RootGUIThread(threading.Thread):

    def run(self):
        layout = [
            [sg.Text('Root Control Panel', size=(30, 1), justification='center', font=("Helvetica", 25),
                     relief=sg.RELIEF_RIDGE)],
            [sg.Button(button_text='Exit')]]

        window = sg.Window('Root Control Panel').Layout(layout)

        print = sg.EasyPrint
        print('Welcome My Lord!')

        while True:
            event, values = window.Read()
            if event is None or event == 'Exit':
                break

        window.Close()


def run():
    server = Peer(ROOT_IP, ROOT_PORT, is_root=True)
    RootGUIThread().start()
    server.run()


if __name__ == '__main__':
    run()
