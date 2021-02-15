if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    import qt5reactor
    qt5reactor.install()
    from camera.client.camera_client import CameraGui
    w = CameraGui()
    w.show()
    sys.exit(app.exec_())
