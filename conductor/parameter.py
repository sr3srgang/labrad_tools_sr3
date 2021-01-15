from collections import deque
from labrad import connect
import traceback

from conductor.exceptions import ParameterInitializationError
from conductor.exceptions import ParameterTerminationError
from conductor.exceptions import ParameterSetValueError
from conductor.exceptions import ParameterGetValueError
from conductor.exceptions import ParameterAdvanceError
from conductor.exceptions import ParameterUpdateError

class ConductorParameter(object):
    """ Base class/template for conductor parameters

    ConductorParameters are meant to provide a nice way to iterate/monitor
         settings/measurements each experimental cycle.

    The methods and properties defined here are all used by the conductor.
    It is therefore recommended that all conductor parameters inherit this class.

    the conductor calls parameters' update with higher priority first. 
    if priority <= 0, update does not get called.

    value_type is used to select preconfigured behaviors of 
        ConductorParameter.{value, advance, remaining_points, ...}
        
        value_type = 'single':
            value is not iterable
        
        value_type = 'list':
            value is list

        value_type = 'once':
            value is anything
            value_queue is None
            value is set to None on advance

        value_type = 'data':
            value is anything
            remaining_points = None

    """
    autostart = False
    call_in_thread = False
    priority = None
    value_type = 'single'
    value = None
    value_queue = deque([])
#    next_value = None
    previous_value = None

    verbose = False
    
    def initialize(self, config={}):
        for k, v in config.items():
            setattr(self, k, v)
        
    def _initialize(self, config={}):
        try:
            return self.initialize(config)
        except:
            traceback.print_exc()
            raise ParameterInitializationError(self.name)
    
    def terminate(self):
        if hasattr(self, 'cxn'):
            self.cxn.disconnect()

    def _terminate(self):
        try:
            return self.terminate()
        except:
            traceback.print_exc()
            raise ParameterTerminationError(self.name)

    def connect_to_labrad(self):
        connection_name = '{} - {}'.format(self.servername, self.name)
        self.cxn = connect(name=connection_name)

    def set_value(self, value):    
        """ set value, and value_queue if we want to scan parameter value """
        if self.value_type == 'single':
            if hasattr(value, '__iter__'):
                self.value_queue = deque([v for v in value])
            else:
                self.value_queue = deque([])
                self.value = value

        elif self.value_type == 'list':
            if not hasattr(value, '__iter__'):
                self.value = value
#                message = (
#                        "conductor parameter ({}) has value_type 'list'."
#                        "trying to assign value with no attr '__iter__'."
#                        .format(self.name)
#                        )
#                raise Exception(message)
            elif len(value) > 1:
                if hasattr(value[0], '__iter__'):
                    self.value_queue = deque([v for v in value])
                else:
                    self.value_queue = deque([])
                    self.value = value
            else:
                self.value_queue = deque([])
                self.value_queue = deque([value])
        
        elif self.value_type == 'dict':
            if type(value).__name__ == 'list':
                self.value_queue = deque([v for v in value])
            else:
                self.value_queue = deque([])
                self.value = value

        elif self.value_type == 'once':
            self.value = value

        elif self.value_type == 'data':
            self.value = value

        return self.value

    def _set_value(self, value):
        try:
            return self.set_value(value)
        except:
            traceback.print_exc()
            raise ParameterSetValueError(self.name)

    def get_value(self):
        return self.value
    
    def _get_value(self):
        try:
            return self.get_value()
        except:
            traceback.print_exc()
            raise ParameterGetValueError(self.name)
    
    def get_next_value(self):
        return self.next_value
    
    def _get_next_value(self):
        try:
            return self.get_next_value()
        except:
            traceback.print_exc()
            raise ParameterGetValueError(self.name)
    
    @property
    def next_value(self):
        if self.value_queue:
            return self.value_queue[0]
        else:
            return self.value

    def advance(self, loop):
        # set previous_value
        self.previous_value = self.value
        
        # set value
        if self.value_queue:
            self.value = self.value_queue.popleft()
        if self.value_type in ['once']:
            self.value = None
        
        # append value to end of queue if looping
        if loop and self.value_queue:
            self.value_queue.append(self.value)

    def _advance(self, loop):
        try:
            return self.advance(loop)
        except:
            traceback.print_exc()
            raise ParameterAdvanceError(self.name)
            
        
    def update(self):
        pass

    def _update(self):
        try:
            return self.update()
        except:
            traceback.print_exc()
            raise ParameterUpdateError(self.name)
