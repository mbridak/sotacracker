# sotacracker
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)  [![Python: 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)  [![Made With:PyQt5](https://img.shields.io/badge/Made%20with-PyQt5-red)](https://pypi.org/project/PyQt5/)

![soda cracker](https://github.com/mbridak/sotacracker/raw/main/pic/soda-cracker.png)

Pulls latest SOTA spots. Displays them in a compact interface. If you have an instance of `rigctld` running, when you click on a spot your radio will automatically tune to the spotted frequency.

Added dropdowns at the top of the screen to filter band and mode.

Written in Python3, using QT5. Either run from source, or if your running Linux, download the binary [here](https://github.com/mbridak/sotacracker/releases/download/21.5.23/sotacracker)

## Running from source.
If you're running from source you can install Python3, then the required moduals PyQt5 and requests, with pip.

`python3 -m pip3 install -r requirements.txt`

![screenshot](https://github.com/mbridak/sotacracker/raw/main/pic/screenshot.png)
