#!/usr/bin/env python3
import requests, sys, os, socket, json
from PyQt5 import QtCore, QtWidgets
from PyQt5 import uic
from datetime import datetime,timezone

class MainWindow(QtWidgets.QMainWindow):
    sotaurl="https://api2.sota.org.uk/api/spots/20/all"
    sotasorteddic={}
    rigctld_addr = "127.0.0.1"
    rigctld_port = 4532

    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(self.relpath("dialog.ui"), self)
        self.listWidget.clicked.connect(self.spotclicked)
        pass

    def relpath(self, filename):
        try:
            base_path = sys._MEIPASS # pylint: disable=no-member
        except:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, filename)

    def getspots(self):
        self.time.setText(str(datetime.now(timezone.utc)).split()[1].split(".")[0][0:5])
        request=requests.get(self.sotaurl,timeout=1.0)
        spots = json.loads(request.text)
        self.listWidget.clear()
        justonce=[]

        for i in spots:
            i['activatorCallsign']=i['activatorCallsign'].replace("\n", "").upper()
            i['activatorCallsign']=i['activatorCallsign'].replace(" ", "")
            if i['activatorCallsign'] in justonce:
                continue
            justonce.append(i['activatorCallsign'])
            summit = f"{i['associationCode'].rjust(3)}/{i['summitCode'].rjust(6)}" # {i['summitDetails']}
            self.listWidget.addItem(f"{i['timeStamp'][11:16]} {i['activatorCallsign'].rjust(10)} {summit.ljust(9)} {i['frequency'].rjust(8)} {i['mode'].upper()}")

    def spotclicked(self):
        """
        If rigctld is running on this PC, tell it to tune to the spot freq.
        Otherwise die gracefully.
        """

        try:
            item = self.listWidget.currentItem()
            line = item.text().split()
            print(line)
            freq = line[3].split(".")
            combfreq = freq[0]+freq[1].ljust(6,'0')
            radiosocket = socket.socket()
            radiosocket.settimeout(0.1)
            radiosocket.connect((self.rigctld_addr, self.rigctld_port))
            command = 'F'+combfreq+'\n'
            radiosocket.send(command.encode('ascii'))
            radiosocket.shutdown(socket.SHUT_RDWR)
            radiosocket.close()
        except:
            pass 

app = QtWidgets.QApplication(sys.argv)
app.setStyle('Fusion')
window = MainWindow()
window.show()
window.getspots()
timer = QtCore.QTimer()
timer.timeout.connect(window.getspots)
timer.start(30000)
app.exec()