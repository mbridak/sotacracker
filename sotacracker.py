#!/usr/bin/env python3
"""Help find and sort SOTA spots, automatically tune radio and set mode via CAT"""

# pylint: disable=c-extension-no-member
# pylint: disable=no-name-in-module

import argparse
import sys
import os
import re
import logging
from datetime import datetime, timezone
from json import loads
import psutil
from PyQt5 import QtCore, QtWidgets, uic
from PyQt5.QtCore import QDir
from PyQt5.QtGui import QFontDatabase
import requests
from lib.cat_interface import CAT

__author__ = "Michael C. Bridak, K6GTE"
__license__ = "GNU General Public License v3.0"

logger = logging.getLogger("__name__")
handler = logging.StreamHandler()
formatter = logging.Formatter(
    datefmt="%H:%M:%S",
    fmt="[%(asctime)s] %(levelname)s %(module)s - %(funcName)s Line %(lineno)d:\n%(message)s",
)
handler.setFormatter(formatter)
logger.addHandler(handler)

parser = argparse.ArgumentParser(
    description=(
        "sotacracker helps chasers hunt SOTA activators.\n"
        "Find out more about SOTA at https://www.sota.org.uk/"
    )
)
parser.add_argument(
    "-s",
    "--server",
    type=str,
    help="Force a server and port address. --server localhost:12345",
)

parser.add_argument(
    "-r",
    action=argparse.BooleanOptionalAction,
    dest="rigctld",
    help="Force use of rigctld",
)

parser.add_argument(
    "-f",
    action=argparse.BooleanOptionalAction,
    dest="flrig",
    help="Force use of flrig",
)

parser.add_argument(
    "-d",
    action=argparse.BooleanOptionalAction,
    dest="debug",
    help="Debug",
)

args = parser.parse_args()

FORCED_INTERFACE = None
SERVER_ADDRESS = None

if args.rigctld:
    FORCED_INTERFACE = "rigctld"
    SERVER_ADDRESS = "localhost:4532"

if args.flrig:
    FORCED_INTERFACE = "flrig"
    SERVER_ADDRESS = "localhost:12345"

if args.server:
    SERVER_ADDRESS = args.server

if args.debug:
    logger.setLevel(logging.DEBUG)

logger.debug("Forced Interface: %s", FORCED_INTERFACE)
logger.debug("Server Address: %s", SERVER_ADDRESS)


def relpath(filename):
    """
    Checks to see if program has been packaged with pyinstaller.
    If so base dir is in a temp folder.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base_path = getattr(sys, "_MEIPASS")
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, filename)


def load_fonts_from_dir(directory):
    """loads in font families"""
    families = set()
    for file_index in QDir(directory).entryInfoList(["*.ttf", "*.woff", "*.woff2"]):
        _id = QFontDatabase.addApplicationFont(file_index.absoluteFilePath())
        families |= set(QFontDatabase.applicationFontFamilies(_id))
    return families


class MainWindow(QtWidgets.QMainWindow):
    """The main window class"""

    sotaurl = "https://api2.sota.org.uk/api/spots/40/all"
    sotasorteddic = {}
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
        self.cat_control = None
        local_flrig = self.check_process("flrig")
        local_rigctld = self.check_process("rigctld")

        if FORCED_INTERFACE:
            address, port = SERVER_ADDRESS.split(":")
            self.cat_control = CAT(FORCED_INTERFACE, address, int(port))

        if self.cat_control is None:
            if local_flrig:
                if SERVER_ADDRESS:
                    address, port = SERVER_ADDRESS.split(":")
                else:
                    address, port = "localhost", "12345"
                self.cat_control = CAT("flrig", address, int(port))
            if local_rigctld:
                if SERVER_ADDRESS:
                    address, port = SERVER_ADDRESS.split(":")
                else:
                    address, port = "localhost", "4532"
                self.cat_control = CAT("rigctld", address, int(port))

    @staticmethod
    def check_process(name: str) -> bool:
        """checks to see if flrig is in the active process list"""
        for proc in psutil.process_iter():
            if bool(re.match(name, proc.name().lower())):
                return True
        return False

    @staticmethod
    def relpath(filename: str) -> str:
        """
        If the program is packaged with pyinstaller,
        this is needed since all files will be in a temp
        folder during execution.
        """
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            base_path = getattr(sys, "_MEIPASS")
        else:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, filename)

    def getspots(self):
        """Gets activator spots"""
        self.time.setText(str(datetime.now(timezone.utc)).split()[1].split(".")[0][0:5])
        spots = False
        try:
            request = requests.get(self.sotaurl, timeout=15.0)
            spots = loads(request.text)
            self.listWidget.clear()
        except requests.exceptions.RequestException:
            return
        justonce = []
        for count, i in enumerate(spots):
            if (
                self.comboBox_mode.currentText() == "All"
                or i["mode"].upper() == self.comboBox_mode.currentText()
            ):
                if (
                    self.comboBox_band.currentText() == "All"
                    or self.getband(i["frequency"].split(".")[0])
                    == self.comboBox_band.currentText()
                ):
                    i["activatorCallsign"] = (
                        i["activatorCallsign"].replace("\n", "").upper()
                    )
                    i["activatorCallsign"] = i["activatorCallsign"].replace(" ", "")
                    if i["activatorCallsign"] in justonce:
                        continue
                    if count > 20:
                        return
                    justonce.append(i["activatorCallsign"])
                    summit = (
                        f"{i['associationCode'].rjust(3)}/{i['summitCode'].rjust(6)}"
                    )
                    spot = (
                        f"{i['timeStamp'][11:16]} {i['activatorCallsign'].rjust(12)} "
                        f"{summit.ljust(9)} {i['frequency'].rjust(8)} {i['mode'].upper()}"
                    )
                    self.listWidget.addItem(spot)
                    if spot[5:] == self.lastclicked[5:]:
                        founditem = self.listWidget.findItems(
                            spot[5:], QtCore.Qt.MatchFlag.MatchContains
                        )
                        founditem[0].setSelected(True)

    def spotclicked(self):
        """
        If rigctld is running on this PC, tell it to tune to the spot freq.
        Otherwise die gracefully.
        """

        item = self.listWidget.currentItem()
        self.lastclicked = item.text()
        if self.cat_control is not None:
            line = item.text().split()
            freq = line[3].split(".")
            mode = line[4].upper()
            combfreq = freq[0] + freq[1].ljust(6, "0")
            self.cat_control.set_vfo(combfreq)
            # self.server.rig.set_frequency(float(combfreq))
            if mode == "SSB":
                if int(combfreq) > 10000000:
                    mode = "USB"
                else:
                    mode = "LSB"
            self.cat_control.set_mode(mode)
            # self.server.rig.set_mode(mode)

    def getband(self, freq):
        """converts freq in mhz to band in meters"""
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
    """Main entry point"""
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    font_dir = relpath("font")
    families = load_fonts_from_dir(os.fspath(font_dir))
    logger.info(families)
    window = MainWindow()
    window.show()
    window.getspots()
    timer = QtCore.QTimer()
    timer.timeout.connect(window.getspots)
    timer.start(30000)
    app.exec()


if __name__ == "__main__":
    main()
