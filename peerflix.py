#!/usr/bin/python
#-*- coding: utf-8 -*-

import sys
import os
import json

from PySide2 import QtCore, QtGui, QtWidgets

__version__ = "1.0.0"


def ui_caller(app_in, executor, ui_class, **kwargs):
    global app
    global ui_instance
    self_quit = False
    try:
        app = QtWidgets.QApplication.instance()
    except TypeError:
        app = None
    if app is None:
        if not app_in:
            try:
                app = QtWidgets.QApplication(sys.argv)
            except (TypeError, AttributeError):  # sys.argv gives argv.error or
                                                 # Qt gives TypeError
                app = QtWidgets.QApplication([])
        else:
            app = app_in
        self_quit = True

    ui_instance = ui_class(**kwargs)
    ui_instance.show()
    if executor is None:
        app.exec_()
        if self_quit:
            app.connect(
                app,
                QtCore.SIGNAL("lastWindowClosed()"),
                app,
                QtCore.SLOT("quit()")
            )
    else:
        executor.exec_(app, ui_instance)
    return ui_instance


class Torrent:
    """Stores Torrent related data
    """

    def __init__(self, raw_data=None):
        self.language = None
        self.durability = None
        self.torrent_url = None
        self.torrent_peers = None
        self.vitality = None
        self.torrent_seeds = None
        self.file = None
        self.torrent_magnet = None
        self.size_bytes = None
        self.quality = None
        self.id = None

        if raw_data:
            self.parse(raw_data)

    def parse(self, raw_data):
        self.id = raw_data.get('id')
        self.language = raw_data.get('language')
        self.durability = raw_data.get('durability')
        self.torrent_url = raw_data.get('torrent_url')
        self.torrent_peers = raw_data.get('torrent_peers')
        self.vitality = raw_data.get('vitality')
        self.torrent_seeds = raw_data.get('torrent_seeds')
        self.file = raw_data.get('file')

        self.torrent_magnet = raw_data['torrent_magnet'].replace("%3A", ":").replace("%2F", "/").replace("u0026", "&")

        self.size_bytes = raw_data.get('size_bytes')
        self.quality = raw_data.get('quality')


class MovieData:
    """Stores movie related data from PopcornTime page
    """

    def __init__(self):
        self._data = None
        self.torrents = []

    def from_url(self, url):
        """extracts data from the given url
        """
        # use urllib2 to get the page source
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
            'Accept-Encoding': 'none',
            'Accept-Language': 'en-US,en;q=0.8',
            'Connection': 'keep-alive'
        }
        if sys.version_info.major == 2:
            from urllib2 import Request, urlopen
        else:
            from urllib.request import Request, urlopen

        req = Request(url, headers=headers)
        page = urlopen(req)
        content = page.read().decode('utf-8')  # This is needed for Python 3

        raw_data = None
        lines = map(str.strip, content.split("\n"))
        for line in lines:
            if line.startswith("fetcher.scrappers"):
                raw_data = line[len("fetcher.scrappers.t4p_movie("):-len(",movies,true,{})")]
                break
        if raw_data:
            self.parse(raw_data)
       
    def parse(self, raw_data):
        """parses raw data
        """
        # get the magnet part of the page
        data = None
        if raw_data:
            data = json.loads(raw_data)

        if not data:
            return

        for item in data['items']:
            self.torrents.append(Torrent(item))

    def get_torrent(self, quality):
        """returns the torrent matching the given quality
        """
        for torrent in self.torrents:
            if torrent.quality == quality:
                return torrent


def cmd():
    """this is the command line interface
    """
    link = sys.argv[1]
    quality = '1080p'

    if len(sys.argv) > 2:
        quality = sys.argv[2]

    watch_command(link, quality)


def watch_command(link, quality='1080p'):
    """the watch command
    """
    # this is the web page
    md = MovieData()
    md.from_url(link)

    torrent = md.get_torrent(quality)

    # call peerflix
    if torrent:
        os.system("peerflix '%s' --vlc -- --fullscreen" % torrent.torrent_magnet)


class MainWindow(QtWidgets.QDialog):
    """The main application
    """

    popcorn_time_site_url = "https://popcorntime-online.ch/"

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.main_layout = None
        self.url_line_edit = None
        self.quality_combo_box = None
        self.watch_push_button = None

        self.setup_ui()

    def setup_ui(self):
        """create UI elements
        """
        self.setWindowTitle("Peerflix UI %s" % __version__)
        self.resize(550, 100)

        # create UI elements
        self.main_layout = QtWidgets.QVBoxLayout(self)

        site_button = QtWidgets.QPushButton(self)
        site_button.setText("Open Popcorn Time Site!!!")
        self.main_layout.addWidget(site_button)

        self.url_line_edit = QtWidgets.QLineEdit(self)
        self.url_line_edit.setPlaceholderText("URL")
        self.main_layout.addWidget(self.url_line_edit)

        self.quality_combo_box = QtWidgets.QComboBox(self)
        self.quality_combo_box.addItem("1080p")
        self.quality_combo_box.addItem("720p")
        self.main_layout.addWidget(self.quality_combo_box)

        self.watch_push_button = QtWidgets.QPushButton(self)
        self.watch_push_button.setText("WATCH !!!")
        self.main_layout.addWidget(self.watch_push_button)

        # setup signals
        QtCore.QObject.connect(
            self.watch_push_button,
            QtCore.SIGNAL('clicked()'),
            self.watch_push_button_clicked
        )

        QtCore.QObject.connect(
            site_button,
            QtCore.SIGNAL('clicked()'),
            self.site_button_clicked
        )

    def watch_push_button_clicked(self):
        """runs when watch push button is clicked
        """
        quality = self.quality_combo_box.currentText()
        print(quality)
        watch_command(link=self.url_line_edit.text(), quality=quality)

    def site_button_clicked(self):
        """runs when the open site button is clicked
        """
        import webbrowser
        webbrowser.open(self.popcorn_time_site_url)


if __name__ == '__main__':
    # use the UI
    ui_caller(None, None, MainWindow)
