if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    import qt5reactor
    qt5reactor.install()

    camera = 'vertical_mot'
    camera_id = 'DEV_000F315D322A'
    from camera.servers.camera_device import Camera
    w = Camera(camera, camera_id)
    #w.show()
    sys.exit(app.exec_())
