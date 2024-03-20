import sys, json, time, os
from shutil import copyfile
import numpy as np
from client_tools.connection3 import connection
from PyQt5 import QtGui, QtCore
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import QDialog, QGridLayout, QLineEdit, QLabel, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout, QWidget, QPushButton
from PyQt5.QtCore import Qt, QTimer, QDateTime
import data_analysis.imaging_tools as it
from datetime import datetime
import warnings
from camera.client.live_plotter_client_beta import LivePlotter
from twisted.internet.defer import inlineCallbacks

import matplotlib.patches as patches
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
#from client_tools.connection import connection

class MplCanvas(FigureCanvas):
    def __init__(self):
        fig, ax = plt.subplots(1)
        self.fig = fig
        self.fig.set_facecolor('k')
        self.ax = ax

        self.fig.set_tight_layout(True)

        FigureCanvas.__init__(self, self.fig)
        self.setFixedSize(1200, 800)

class CameraGui(QDialog):
    def set_vars(self):
        self.camera = 'top_monitor'
        self.name = self.camera
        self.fluorescence_mode = True
        self.update_id = np.random.randint(0, 2**31 - 1)
        self.ROI = None
        self.no_lim = True
    
    def __init__(self):
        super(CameraGui, self).__init__(None)
        self.set_vars()
        self.connect_to_labrad()
        self.loadButtonState = False  # Track the toggle state of the "Load" button
        self.populate()
        self.Plotter = LivePlotter(self)  
    
    def populate(self):
        self.setWindowTitle("Camera GUI")
        self.canvas = MplCanvas()
        
        self.nav = NavigationToolbar(self.canvas, self)
        
        # Table initialization with custom font size for labels
        self.paramsTable = QTableWidget(4, 3)
        self.paramsTable.setHorizontalHeaderLabels(['Label', 'X Parameters', 'Y Parameters'])
        self.paramsTable.setFixedSize(400, 150)
        labelFont = QFont()
        labelFont.setPointSize(14)  # Font size for table labels
        labels = ['Amplitude', 'Center', 'Sigma', 'Offset']
        for i, label in enumerate(labels):
            labelItem = QTableWidgetItem(label)
            labelItem.setFont(labelFont)
            self.paramsTable.setItem(i, 0, labelItem)
        
        # "Save" button with custom font size
        self.saveButton = QPushButton("Save")
        buttonFont = QFont()
        buttonFont.setPointSize(16)  # Font size for buttons
        self.saveButton.setFont(buttonFont)
        self.saveButton.clicked.connect(self.save_vals)
        
        # "Load" button initialization with custom font size
        self.loadButton = QPushButton("Load")
        self.loadButton.setFont(buttonFont)
        self.loadButton.clicked.connect(self.toggle_load_button)
        
        # Layout for buttons
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.saveButton)
        buttonLayout.addWidget(self.loadButton)
        
        # Layout for parameters table and buttons
        paramsLayout = QVBoxLayout()
        paramsLayout.addWidget(self.paramsTable)
        paramsLayout.addLayout(buttonLayout)
        paramsLayout.addStretch(1)  # Push everything up
        
        # Main layout
        mainLayout = QHBoxLayout()
        plotLayout = QVBoxLayout()
        plotLayout.addWidget(self.nav)
        plotLayout.addWidget(self.canvas)
        plotLayout.addStretch(1)
        
        mainLayout.addLayout(plotLayout)
        paramsWidget = QWidget()
        paramsWidget.setLayout(paramsLayout)
        mainLayout.addWidget(paramsWidget, 1)
        
        self.setLayout(mainLayout)
        self.adjustSize()
        
    def toggle_load_button(self):
        self.loadButtonState = not self.loadButtonState  # Toggle the state
        
        if self.loadButtonState:
            # When the Load button is toggled on
            self.loadButton.setStyleSheet("background-color: green;")
            self.loadButton.setText("Loaded")
        else:
            # When the Load button is toggled off
            self.loadButton.setStyleSheet("")  # Clear custom styles
            self.loadButton.setText("Load")
        
        self.show_window()  # Update the window to reflect the current state 
        
    #Labrad connection:
    @inlineCallbacks    
    def connect_to_labrad(self):
        #self.cxn = connect(name=self.name)
        self.cxn = connection()
        yield self.cxn.connect(name = 'camera viewer')
        server = yield self.cxn.get_server('camera')
        yield server.signal__update(self.update_id)
        yield server.addListener(listener = self.receive_update, source=None, ID=self.update_id)
        print('connected')
        
    def receive_update(self, c, update_json):
        update = json.loads(update_json)
        for key, value in update.items():
            if key == self.camera:
                if self.fluorescence_mode:
                    if not (('exc' in value[0]) or ('background' in value[0])):
                        print(value)
                        if 'gnd' in value[0]:
                            print(value[0])
                            str_end = '_fluorescence.png'
                            keyword = 'vertical_mot_fluor_'
                            split_str = value[0].partition(str_end)
                            parse_name = split_str[0].partition(keyword)
                            print(parse_name)
                            beginning = parse_name[0]
                            shot_num = int(parse_name[-1])
                            offset = 3
                            mod_shot = shot_num - offset
                            new_path = beginning + keyword + str(mod_shot) + str_end
                            print(new_path)
                            self.file_to_show = new_path#value[0]
                        else:
                            self.file_to_show = value[0]
                        print(self.file_to_show)
                        

                        time.sleep(.1)
                        self.Plotter.show_window()
                        self.show_window()                       
    
    def show_window(self):
        if not self.no_lim:
            xlim = self.canvas.ax.get_xlim()
            ylim = self.canvas.ax.get_ylim()
        else:
            xlim = None
            ylim = None
        
        # Simulate the calculation and formatting of vals_x and vals_y
        # In your actual code, vals_x and vals_y would be obtained from your image processing function
        vals_x, vals_y = it.fig_gui_window_ROI_with_fitting(self.file_to_show, self.canvas.ax, xlim, ylim)
        self.vals_x = vals_x
        self.vals_y = vals_y
        
        # Assuming vals_x and vals_y are formatted as strings; convert them if they are not
        vals_x_str = ', '.join(f"{x:.3f}" for x in vals_x)
        vals_y_str = ', '.join(f"{y:.3f}" for y in vals_y)
        
        # Define the font for the table items
        font = QFont()
        font.setPointSize(16)  # Set the desired text size

        # Insert vals_x and vals_y into the table
        for i, (x_val, y_val) in enumerate(zip(vals_x, vals_y)):
            self.paramsTable.setItem(i, 1, QTableWidgetItem(f"{x_val:.3f}"))
            self.paramsTable.setItem(i, 2, QTableWidgetItem(f"{y_val:.3f}"))
            # Set the font for new items
            for col in range(1, 3):  # Skip the label column
                item = self.paramsTable.item(i, col)
                if item:
                    item.setFont(font)

        # Adjust the plot limits if necessary
        if not self.no_lim:
            self.canvas.ax.set_xlim(xlim)
            self.canvas.ax.set_ylim(ylim)
        else:
            self.no_lim = False
            
        try:    
            if self.loadButtonState:
                self.load_vals()  # Call load_vals only when the Load button is toggled on
        except:
            print("Failed to load historical data.")

        # Update the plot title and redraw
        self.canvas.ax.set_title("{:.3e}".format(self.Plotter.title), color='w', y=.85, size=42)
        self.canvas.draw()
        print('redrawn')
        
    def launch_plotter(self):
        self.Plotter.show()
        
    def save_vals(self):
        # Format the current time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Assuming vals_x and vals_y are stored as attributes of the class
        # Convert them to strings
        vals_x_str = ', '.join(f"{x:.3f}" for x in self.vals_x)
        vals_y_str = ', '.join(f"{y:.3f}" for y in self.vals_y)
        
        # Specify the Windows file path
        filename = r"C:\Users\srgang\labrad_tools\camera\client\Top_Monitor_Historical_Markers.txt"
        
        # Open the file in append mode and write the current time, followed by vals_x and vals_y
        with open(filename, "a+") as file:
            file.write(f"Current Time: {current_time}\n")
            file.write(f"Vals X: {vals_x_str}\n")
            file.write(f"Vals Y: {vals_y_str}\n\n")
        
        print(f"Values appended to {filename}")
        
    def load_vals(self):
        filename = 'C:/Users/srgang/labrad_tools/camera/client/Top_Monitor_Historical_Markers.txt'
        with open(filename, 'r') as file:
            lines = file.readlines()

        ellipse_count = 0
        for i in range(0, len(lines), 4):  # Assuming each record spans 4 lines (including the blank line)
            if lines[i].startswith('Current Time:'):
                # Extract vals_x and vals_y
                vals_x_str = lines[i+1].split(": ")[1].strip()
                vals_y_str = lines[i+2].split(": ")[1].strip()
                vals_x = [float(val) for val in vals_x_str.strip('[]').split(', ')]
                vals_y = [float(val) for val in vals_y_str.strip('[]').split(', ')]
                
                # Assuming vals_x and vals_y format: [A, mean, sigma, C]
                mean_x, sigma_x = vals_x[1], vals_x[2]
                mean_y, sigma_y = vals_y[1], vals_y[2]

                # Plot ellipses based on the Gaussian fitting parameters
                # Here I changed the size of the ellipse to 5* for debugging, change the width and height to 3* when needed.
                ellipse = patches.Ellipse((mean_x, mean_y), width=5*sigma_x, height=5*sigma_y,
                                          angle=0, fill=False, edgecolor='red', lw=1, alpha=0.4, linestyle='--')
                self.canvas.ax.add_patch(ellipse)
                
                # Draw a red cross at the fitted center
                cross_size = 1*sigma_x  # Adjust size as needed
                self.canvas.ax.plot(mean_x, mean_y, 'r+', markersize=cross_size, markeredgewidth=1, alpha=0.4)
                
                ellipse_count += 1
                # Add a number label to the upper right of each ellipse
                self.canvas.ax.text(mean_x + 2*sigma_x, mean_y + 2*sigma_y, str(ellipse_count),
                                    color='red', fontsize=16, ha='right', va='top', alpha=0.4)

        self.canvas.draw()
        print("Historical data loaded and plotted with ellipses.")
