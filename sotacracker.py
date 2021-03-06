#!/usr/bin/env python3

import logging
logging.basicConfig(level=logging.WARNING)

import xmlrpc.client
import requests, sys, os
from json import loads
from PyQt5 import QtCore, QtWidgets, uic
from PyQt5.QtCore import QDir
from PyQt5.QtGui import QFontDatabase
from datetime import datetime,timezone

def relpath(filename):
		try:
			base_path = sys._MEIPASS # pylint: disable=no-member
		except:
			base_path = os.path.abspath(".")
		return os.path.join(base_path, filename)

def load_fonts_from_dir(directory):
		families = set()
		for fi in QDir(directory).entryInfoList(["*.ttf", "*.woff", "*.woff2"]):
			_id = QFontDatabase.addApplicationFont(fi.absoluteFilePath())
			families |= set(QFontDatabase.applicationFontFamilies(_id))
		return families

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
        self.server = xmlrpc.client.ServerProxy("http://localhost:12345")

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
            spots = loads(request.text)
            self.listWidget.clear()
        except:
            return
        justonce=[]
        for count, i in enumerate (spots):
            if self.comboBox_mode.currentText() == 'All' or i['mode'].upper() == self.comboBox_mode.currentText():
                if self.comboBox_band.currentText() == 'All' or self.getband(i['frequency'].split('.')[0]) == self.comboBox_band.currentText():
                    i['activatorCallsign']=i['activatorCallsign'].replace("\n", "").upper()
                    i['activatorCallsign']=i['activatorCallsign'].replace(" ", "")
                    if i['activatorCallsign'] in justonce:
                        continue
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
            self.server.rig.set_frequency(float(combfreq))
            if mode == 'SSB':
                if int(combfreq) > 10000000:
                    mode = 'USB'
                else:
                    mode = 'LSB'
            self.server.rig.set_mode(mode)
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
    font_dir = relpath("font")
    families = load_fonts_from_dir(os.fspath(font_dir))
    logging.info(families)
    window = MainWindow()
    window.show()
    window.getspots()
    timer = QtCore.QTimer()
    timer.timeout.connect(window.getspots)
    timer.start(30000)
    app.exec()

if __name__ == "__main__":
    main()