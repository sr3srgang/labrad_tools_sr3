"""
### BEGIN NODE INFO
[info]
name = plotter
version = 1.0
description = 
instancename = plotter

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

import imp
import json
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import os
import StringIO
from time import time
import numpy as np
from pathlib import Path
import matplotlib.gridspec as gridspec

from autobahn.twisted.websocket import WebSocketServerProtocol
from autobahn.twisted.websocket import WebSocketServerFactory
from labrad.server import setting
from twisted.internet import reactor


from server_tools.threaded_server import ThreadedServer

WEBSOCKET_PORT = 9000

class MyServerProtocol(WebSocketServerProtocol):
    connections = list()

    def onConnect(self, request):
        self.connections.append(self)
        print("Client connecting: {0}".format(request.peer))

    def onOpen(self):
        print("WebSocket connection open.")
    
    @classmethod
    def send_figure(cls, figure):
    #def send_figure(cls):
        print('num connections', len(cls.connections))
#       figure = "figure"
        for c in set(cls.connections):
            reactor.callFromThread(cls.sendMessage, c, figure, False)
    
    @classmethod
    def close_all_connections(cls):
        for c in set(cls.connections):
            reactor.callFromThread(cls.sendClose, c)
    
    def onMessage(self, payload, isBinary):
        if isBinary:
            print("Binary message received: {0} bytes".format(len(payload)))
        else:
            print("Text message received: {0}".format(payload.decode('utf8')))

        # echo back message verbatim
        self.sendMessage(payload, isBinary)

    def onClose(self, wasClean, code, reason):
        self.connections.remove(self)
        print("WebSocket connection closed: {0}".format(reason))

class PlotterServer(ThreadedServer):
    name = 'plotter'
    is_plotting = False

    def initServer(self):
        """ socket server """
        url = u"ws://0.0.0.0:{}".format(WEBSOCKET_PORT)
        factory = WebSocketServerFactory()
        factory.protocol = MyServerProtocol
        reactor.listenTCP(WEBSOCKET_PORT, factory)
        #fig, ax = plt.subplots(2,2)
	self.init_fig()
        self.current_expt = ''
    
    def init_fig(self):
        fig = plt.figure(figsize = (12,8))
        plt.rcParams.update({'font.size':16})

        gs = gridspec.GridSpec(ncols = 2, nrows = 3)#, figure = fig)
        fig.patch.set_facecolor('black')
        #gs = fig.add_gridspec(3, 2)
        ax_trace = fig.add_subplot(gs[0, :])#, gridspec_kw = {'height_ratios': [1, 3]})
        ax_trace.set_facecolor('xkcd:pinkish grey')
        ax_freq = fig.add_subplot(gs[1:, 0])
        ax_freq.set_facecolor('xkcd:pinkish grey')
        ax_shot = fig.add_subplot(gs[1:, 1])
	ax_shot.set_facecolor('xkcd:pinkish grey')
#	fig = plt.figure()
        self.my_fig = fig
        self.data_x = []
        self.data_y = []
        self.my_ax = [ax_freq, ax_shot, ax_trace]
	for ax in self.my_ax:
		ax.yaxis.label.set_color('white')      
		ax.xaxis.label.set_color('white')   
#		plt.setp([ax.get_xticklines(), ax.get_yticklines()], color='white')
		ax.tick_params(color = 'green', labelcolor = 'white')
        
    def stopServer(self):
        """ socket server """
        MyServerProtocol.close_all_connections()

    @setting(0)
    def plot(self, c, settings_json='{}'):
        settings = json.loads(settings_json)
        if not self.is_plotting:
            reactor.callInThread(self._plot, settings)
            #self._plot(settings)
        else:
            print('still making previous plot')

    def _plot(self, settings):
        try:
            self.is_plotting = True
#            print(settings)
            
            #Reset the plotter if the experiment changes
            this_expt = settings['exp_name']
            if self.current_expt != this_expt:
            	self.current_expt = this_expt
            	self.init_fig()

            
            print('plotting')
            path = settings['plotter_path']             
            function_name = settings['plotter_function'] # name of function that will process data
            module_name = "plot_test"
            print(path)
            print(module_name)
            module = imp.load_source(module_name, path)
            function = getattr(module, function_name)
            fig, x, y= function(settings, self.my_fig, self.my_ax, self.data_x, self.data_y)
            self.data_x = x
            self.data_y = y
            sio = StringIO.StringIO()
            fig.savefig(sio, format='svg', facecolor = 'black')
            sio.seek(0)
            figure_data = sio.read()
            MyServerProtocol.send_figure(figure_data)
            #MyServerProtocol.send_figure()
            print('done plotting')
            print(settings['maxShots'])
#            print settings['freqRange']
#        except Exception as e:
#            raise e
#            print 'failed plotting'
        finally:
            self.is_plotting = False
            try:
                plt.close(fig)
                del fig
                del sio
                del figure_data
            except:
                pass
                

Server = PlotterServer

if __name__ == "__main__":
    from labrad import util
    util.runServer(Server())
