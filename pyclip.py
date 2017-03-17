#!/usr/bin/env python3
"""

.. _Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html
   http://sphinxcontrib-napoleon.readthedocs.org/en/latest/example_google.html
"""
import sys
sys.dont_write_bytecode = True

import signal
import builtins

from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5 import QtWidgets

from tempfile import NamedTemporaryFile
from subprocess import call

from animated_system_tray import AnimatedSystemTrayIcon
from image_viewer import ImageViewer

class TextEditor(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(TextEditor, self).__init__(*args, **kwargs)
        self.edit = QtWidgets.QTextEdit()
        self.setCentralWidget(self.edit)
        self.edit.textChanged.connect(self.text_changed_handler)

    def text_changed_handler(self):
        self.clipboard.setText(self.edit.toPlainText(), self.clipboardMode)

    def open(self, clipboard, mode):
        self.clipboard = clipboard
        self.clipboardMode = mode
        self.edit.setText(clipboard.mimeData(mode).text())
        self.show()

class Gui(QtWidgets.QApplication):
    # signals need to be class variables
    start_animation = QtCore.pyqtSignal()

    def __init__(self):
        builtins.super(self.__class__, self).__init__([])

        self.window = QtWidgets.QWidget()
        self.tray_icon = AnimatedSystemTrayIcon('clipboard.svg', parent=self.window)

        self.clipboard = QtWidgets.QApplication.clipboard()
        self.clipboard.changed.connect(self.clipboard_changed_handler)

        self.build_gui()

        self.imageViewer = ImageViewer()
        self.textEditor = TextEditor()

        self.update_clipboard_content(self.clipboard.Clipboard)
        self.update_clipboard_content(self.clipboard.Selection)

        self.setQuitOnLastWindowClosed(False)

    def clipboard_changed_handler(self, mode):
        self.update_clipboard_content(mode)
        self.tray_icon.get_animator('shrink', repeat=False)()

    def take_screenshot(self):
        f = NamedTemporaryFile(suffix='.png')
        call(['scrot', '-s', f.name])
        image = QtGui.QImage(f.name)
        self.clipboard.setImage(image)

    def update_clipboard_content(self, mode):
        mimeData = self.clipboard.mimeData(mode)
        typeInfo = 'unknown'
        if mimeData.hasText():
            typeInfo = 'text'
        if mimeData.hasImage():
            typeInfo = 'image'
        if mode == self.clipboard.Clipboard:
            self.clipboardItem.setText('clipboard: ' + typeInfo)
        if mode == self.clipboard.Selection:
            self.selectionItem.setText('selection: ' + typeInfo)

    def inspect(self, mode):
        mimeData = self.clipboard.mimeData(mode)
        if mimeData.hasText():
            self.textEditor.open(self.clipboard, mode)
        if mimeData.hasImage():
            self.imageViewer.open_from_clipboard(self.clipboard, mode)

    def build_gui(self):
        menu = QtWidgets.QMenu()
        for (entry, action) in [
            ('take screenshot', self.take_screenshot),
            ('quit', self.quit),
        ]:
            q_action = QtWidgets.QAction(entry, self)
            q_action.triggered.connect(action)
            menu.addAction(q_action)

        menu.addSeparator()
        menu.setSeparatorsCollapsible(True)

        self.clipboardItem = QtWidgets.QAction('', self)
        self.clipboardItem.triggered.connect(
                lambda: self.inspect(self.clipboard.Clipboard)
        )
        menu.addAction(self.clipboardItem)

        self.selectionItem = QtWidgets.QAction('', self)
        self.selectionItem.triggered.connect(
                lambda: self.inspect(mode = self.clipboard.Selection)
        )
        menu.addAction(self.selectionItem)


        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()

    def quit(self, *args, **kwargs):
        QtWidgets.qApp.quit()



if __name__ == '__main__':
    app = Gui()

    # handle sigint gracefully
    signal.signal(signal.SIGINT, app.quit)
    # needed to catch the signal (http://stackoverflow.com/a/4939113/2972353)
    timer = QtCore.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)  # Let the interpreter run each 500 ms.

    # start the app
    sys.exit(app.exec_())
