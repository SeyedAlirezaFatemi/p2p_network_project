import threading

import PySimpleGUI as sg

from RunRoot import ROOT_ADDRESS
from src.Peer import Peer


class GUIThread(threading.Thread):
    def __init__(self, client: Peer) -> None:
        threading.Thread.__init__(self)
        self.client = client

    def run(self):
        layout = [
            [sg.Text('Client Control Panel', size=(30, 1), justification='center', font=("Helvetica", 25),
                     relief=sg.RELIEF_RIDGE)],
            [sg.Button(button_text='Register'), sg.Button(button_text='Advertise')],
            [sg.Input(key='message', tooltip="Enter Message Here", justification='center')],
            [sg.Button(button_text='SendMessage')],
            [sg.Button(button_text='Exit')]]

        window = sg.Window('Control Panel').Layout(layout)

        print = sg.EasyPrint
        print('Welcome My Lord!')

        while True:
            event, values = window.Read()
            if event is None or event == 'Exit':
                break
            if event == 'Register':
                self.client.handle_register_command()
            elif event == 'SendMessage':
                message = values['message']
                self.client.handle_message_command(f'SendMessage {message}')
            elif event == 'Advertise':
                self.client.handle_advertise_command()

        window.Close()


def run():
    client = Peer("127.0.0.1", 1012, is_root=False,
                  root_address=ROOT_ADDRESS, command_line=False)
    GUIThread(client).start()
    client.run()


if __name__ == '__main__':
    run()
