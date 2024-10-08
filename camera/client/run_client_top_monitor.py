if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    from PyQt5 import QtGui
    import sys
    app = QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon('icon_image_cam.png'))
    import qt5reactor
    qt5reactor.install()
    from camera.client.camera_client_top_monitor import CameraGui
    w = CameraGui()
    w.show()
    sys.exit(app.exec_())
