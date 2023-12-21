import numpy as np
from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QPushButton, QLineEdit

class TimeWindowSetter(QWidget):
    
    def __init__(self, parent):
        super(TimeWindowSetter, self).__init__()
        self.parent = parent
        self.entries = self.parent.time_settings #dictionary setting time windows
        self.labels = [QLabel(key) for key in self.entries.keys()]
        self.vals = [self.new_lineEdit(key, value) for key, value in self.entries.items()]
        layout = QGridLayout()
        for i in np.arange(len(self.entries)):
            layout.addWidget(self.labels[i], i, 0)
            layout.addWidget(self.vals[i], i, 1)
            self.setLayout(layout)
            
        
    def new_lineEdit(self, key, value):
        button = QLineEdit(self)
        button.setText(str(value))
        button.returnPressed.connect(self.buttonEntered(key))
        return button
    
    def buttonEntered(self, key):
        def helper():
            ix = list(self.entries.keys()).index(key)
            current_val = self.entries[key]
            try:
                new_val = np.float(self.vals[ix].text())
                self.entries[key] = new_val
            except:
                print('Invalid value entered for ' + key)
            
        return helper
        
