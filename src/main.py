#!/usr/bin/env python3

import sys, gi, utils
from gi.repository import Gtk
from MainWindow import MainWindow

gi.require_version("Gtk", "3.0")


class Application(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, application_id="tr.org.pardus.welcome", **kwargs)
        self.window = None

    def do_activate(self):
        self.window = MainWindow(self)


if __name__ == "__main__":
    if utils.check_live():
        exit(0)
    app = Application()
    app.run(sys.argv)
