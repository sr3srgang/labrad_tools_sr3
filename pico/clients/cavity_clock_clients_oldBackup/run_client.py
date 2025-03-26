if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    import qt5reactor
    qt5reactor.install()
    from pico.clients.cavity_clock_clients_oldBackup.cavity_clock import CavityClockGui
    w = CavityClockGui()
    w.show()
    sys.exit(app.exec_())
