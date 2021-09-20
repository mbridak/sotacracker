#!/usr/bin/env python3
import requests, sys, os, socket, json
from PyQt5 import QtCore, QtWidgets
from PyQt5 import uic
from datetime import datetime,timezone

class MainWindow(QtWidgets.QMainWindow):
    sotaurl="https://api2.sota.org.uk/api/spots/40/all"
    sotasorteddic={}
    rigctld_addr = "127.0.0.1"
    rigctld_port = 4532
    bw = {}
    lastclicked = ""

    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(self.relpath("dialog.ui"), self)
        self.listWidget.clicked.connect(self.spotclicked)
        self.comboBox_band.currentTextChanged.connect(self.getspots)
        self.comboBox_mode.currentTextChanged.connect(self.getspots)
        self.bw['LSB'] = '2400'
        self.bw['USB'] = '2400'
        self.bw['FM'] = '15000'
        self.bw['CW'] = '200'

    def relpath(self, filename):
        try:
            base_path = sys._MEIPASS # pylint: disable=no-member
        except:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, filename)

    def getspots(self):
        self.time.setText(str(datetime.now(timezone.utc)).split()[1].split(".")[0][0:5])
        spots = False
        try:
            request=requests.get(self.sotaurl,timeout=15.0)
            spots = json.loads(request.text)
            self.listWidget.clear()
        except:
            return
        justonce=[]
        count = 0
        for i in spots:
            if self.comboBox_mode.currentText() == 'All' or i['mode'].upper() == self.comboBox_mode.currentText():
                if self.comboBox_band.currentText() == 'All' or self.getband(i['frequency'].split('.')[0]) == self.comboBox_band.currentText():
                    i['activatorCallsign']=i['activatorCallsign'].replace("\n", "").upper()
                    i['activatorCallsign']=i['activatorCallsign'].replace(" ", "")
                    if i['activatorCallsign'] in justonce:
                        continue
                    count += 1
                    if count > 20:
                        return
                    justonce.append(i['activatorCallsign'])
                    summit = f"{i['associationCode'].rjust(3)}/{i['summitCode'].rjust(6)}" # {i['summitDetails']}
                    spot = f"{i['timeStamp'][11:16]} {i['activatorCallsign'].rjust(12)} {summit.ljust(9)} {i['frequency'].rjust(8)} {i['mode'].upper()}"
                    self.listWidget.addItem(spot)
                    if spot[5:] == self.lastclicked[5:]:
                        founditem = self.listWidget.findItems(spot[5:], QtCore.Qt.MatchFlag.MatchContains)
                        founditem[0].setSelected(True)

    def spotclicked(self):
        """
        If rigctld is running on this PC, tell it to tune to the spot freq.
        Otherwise die gracefully.
        """

        try:
            item = self.listWidget.currentItem()
            self.lastclicked = item.text()
            line = item.text().split()
            freq = line[3].split(".")
            mode = line[4].upper()
            combfreq = freq[0]+freq[1].ljust(6,'0')
            radiosocket = socket.socket()
            radiosocket.settimeout(0.1)
            radiosocket.connect((self.rigctld_addr, self.rigctld_port))
            command = 'F'+combfreq+'\n'
            radiosocket.send(command.encode('ascii'))
            if mode == 'SSB':
                if int(combfreq) > 10000000:
                    mode = 'USB'
                else:
                    mode = 'LSB'
            command = 'M '+mode+ ' ' + self.bw[mode] + '\n'
            radiosocket.send(command.encode('ascii'))
            radiosocket.shutdown(socket.SHUT_RDWR)
            radiosocket.close()
        except:
            pass 
    
    def getband(self, freq):
        if freq.isnumeric():
            frequency = int(freq)
            if frequency == 1 or frequency == 2:
                return "160"
            if frequency == 3 or frequency == 4:
                return "80"
            if frequency == 5:
                return "60"
            if frequency == 7:
                return "40"
            if frequency == 10:
                return "30"
            if frequency == 14:
                return "20"
            if frequency == 18:
                return "17"
            if frequency == 21:
                return "15"
            if frequency == 24:
                return "12"
            if frequency == 28 or frequency == 29:
                return "10"
            if frequency >= 50 and frequency <= 54:
                return "6"
            if frequency >= 144 and frequency <= 148:
                return "2"
        else:
            return "0"

def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MainWindow()
    window.show()
    window.getspots()
    timer = QtCore.QTimer()
    timer.timeout.connect(window.getspots)
    timer.start(30000)
    app.exec()

if __name__ == "__main__":
    main()