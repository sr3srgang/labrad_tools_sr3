"""
### BEGIN NODE INFO
[info]
name = conductor
version = 1.0
description = 
instancename = conductor

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""
from collections import deque
import glob
import importlib
import json
import os
import sys
import time
import traceback

from server_tools.threaded_server import ThreadedServer
from labrad.server import setting
from labrad.server import Signal
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks
from twisted.internet.reactor import callInThread
from twisted.internet.reactor import callLater

from conductor.exceptions import ParameterImportError
from conductor.exceptions import ParameterNotActiveError
from conductor.exceptions import ParameterNotFoundError
from conductor.exceptions import ParameterValueNotFoundError
from conductor.exceptions import ParameterAlreadyActiveError
from conductor.exceptions import ParameterInitializationError
from conductor.exceptions import ParameterTerminationError
from conductor.exceptions import ParameterReloadError
from conductor.exceptions import ParameterAdvanceError
from conductor.exceptions import ParameterUpdateError
from conductor.exceptions import ParameterSetValueError
from conductor.exceptions import ParameterGetValueError
from conductor.exceptions import ExperimentAdvanceError
from conductor.exceptions import AlreadyAdvancingError
from conductor.exceptions import AdvanceError
from conductor.helpers import sort_by_priority
from conductor.helpers import get_remaining_points
from conductor.parameter import ConductorParameter

# threads are used for executing parameter updates asynchronously
# "threadPoolSize" limits number of parameter updates that can 
# happen at the same time. More threads are better but each thread 
# needs a certain amount of computational resources. 10 - 20 is probably
# a good number.
reactor.suggestThreadPoolSize(10)

class ConductorServer(ThreadedServer):
    """ A server to coordinate running experiemnts.

    Our general task in running a cold atom experiment is to set the outputs of 
    various pieces of hardware, record the inputs from various other pieces of 
    hardware, maybe do some data processing and decision making, record the 
    data, then repeat. This server aims to facilitate such behaviour in a 
    flexible and dynamic way.

    We handle the performance of varous tasks by creating "parameters". A 
    parameter is an object with a few default methods that get called during 
    various stages of each experimental cycle. A more complete description can 
    be found in the class definition (conductor/conductor_parameter.py), but 
    basic behavior is additionally described here.
    ConductorParameter:
        value:
            A simple string, list, dict, float describing the state of a 
            parameter. Values can be placed into a queue to be iterated through
            each cycle of the experiment.
        initialize:
            called once upon loading of parameter. can use this to make various 
            connections to other servers, configure hardware properties, etc.
        advance:
            called once, at the begining of each cycle of the experiment to pull
            the next value specified in the value_queue
        update:
            called once, at the begining of each cycle of the experiment.
            can be used to change outputs of hardware, save data.
        terminate:
    
    This server then serves as a means to interface with these parameters mostly
    by just making the above methdods available over labrad.

    We additionally define "experiments" which are essentially just collections
    of information, specifying which parameters to initialize, and which values 
    to queue.
    """
    name = 'conductor'
    update = Signal(648324, 'signal: update', 's')
    parameters = {}
    experiment = {}
    experiment_queue = deque([])
    parameter_directory = os.path.join(os.getenv('PROJECT_LABRAD_TOOLS_PATH'), name, 'parameters/')
    experiment_directory = os.path.join(os.getenv('PROJECT_LABRAD_TOOLS_PATH'), name, '.experiments/')
    is_advancing = False
    verbose = False

    def initServer(self):
        self._initialize_parameters(request={}, all=True, suppress_errors=True)
    
    def stopServer(self):
        self._save_parameter_values()
        self._terminate_parameters(request={}, all=True, suppress_errors=True)

    @setting(0)
    def get_configured_parameters(self, c):
        """ Get names of parameters available to the conductor.

        This method makes the private method 
        "_get_configured_parameters", available over labrad. Look at 
        that method's documentation for exactly how to configure 
        conductor parameters.

        Args:
            None

        Returns:
            (str) json dumped dict {<(str) parameter_name>: None}
        """
        response = self._get_configured_parameters()
        self._send_update({'get_configured_parameters': response})
        response_json = json.dumps(response, default=lambda x: None)
        return response_json
    
    def _get_configured_parameters(self, suppress_errors=False):
        """ Get names of parameters available to the conductor.
        
        Look in directory "self.parameter_directory" for configured parameters.
        A parameter is configured by having a python module placed in 
        "self.parameters_path" with an assignment, "Parameter = SomeParameterClass".
        the defined Parameter should inherit the parent class "ConductorParameter"
        from "labrad_tools/conductor/conductor_parameter.py"
        to ensure correct behavior by default.

        The parameter directory can be structured as follows.

        parameter1.py
        group1/
            parameter1.py
            parameter2.py
        group2/
            subgroup1/
                parameter1.py
        etc...

        this then corresponds to the following parameter names:
        parameter1, group1.parameter1, group1.parameter2, group2.subgroup1.parameter1

        Args:
            None
        Returns:
            (dict) {<(str) parameter_name>: <ParameterClass>}
        """
        response = {}
        
        parameter_names = []
        for r, d, f in os.walk(self.parameter_directory):
            for file in f:
                full_path = os.path.join(r, file)
                relative_path = full_path.replace(self.parameter_directory, '')
                if file.endswith('__init__.py'):
                    pass
                elif file.endswith('.py'):
                    dotted_relative_path = relative_path.replace('.py', '').replace('/', '.')
                    parameter_names.append(dotted_relative_path)
        
        for parameter_name in parameter_names:
            try:
                ParameterClass = self._import_parameter(parameter_name)
                if ParameterClass:
                    response.update({parameter_name: ParameterClass})
            except ParameterImportError:
                traceback.print_exc()
            except:
                if not suppress_errors:
                    raise
        return response
    
    @setting(1)
    def get_active_parameters(self, c):
        """ Get names of parameters actively being managed by the conductor.

        This method makes the private method "_get_active_parameters" available
        over labrad. Look at that method's documentation for exactly how we 
        determine which parameters are active.

        Args:
            None

        Returns:
            (str) json dumped dict {<(str) parameter_name>: None}
        """
        response = self._get_active_parameters()
        self._send_update({'get_active_parameters': response})
        response_json = json.dumps(response, default=lambda x: None)
        return response_json
    
    def _get_active_parameters(self, suppress_errors=False):
        """ Get names of parameters actively being managed by the conductor.

        parameters are stored in the attribute self.parameters

        Args:
            None
        Returns:
            (dict) {<(str) parameter_name>: <parameter>}
        """
        try:
            return self.parameters
        except:
            if not suppress_errors:
                raise

    @setting(2, request_json='s', all='b')
    def initialize_parameters(self, c, request_json='{}', all=False):
        """ initialize parameters specified in the request 
        
        This method makes the private method "_initialize_parameters" available
        over labrad. Look at that method's documentation for exactly how 
        the parameters are initialized.
        
        Args:
            (str) request_json: A json dumped dict specifying
                {parameter_name: additional_parameter_configuration}
            (bool) all: if True, load all configured parameters with class
                attribute autostart = True.

        Returns:
            (str) json dumped dict 
                {<(str) parameter_name>: <initialization_response>}
            
        """
        request = json.loads(request_json)
        response = self._initialize_parameters(request, all)
        self._send_update({'initialize_parameters': response})
        response_json = json.dumps(response, default=lambda x: None)
        return response_json
    
    def _initialize_parameters(self, request={}, all=False, 
                               suppress_errors=False):
        """ initialize parameters specified in the request.
        
        Args:
            (dict) request: specifies {parameter_name: parameter_config}
                where parameter_config is itself a dict whose (key, value) pairs 
                will be set as attributes of the class instance upon 
                initialization.
            (bool) all: if True, load all configured parameters with class 
                attribute, autostart = True.
        Returns:
            (dict) {<(str) parameter_name>: <initialization_response>}
                where initialization_response is the returned value of 
                <parameter>.initialize(parameter_config)
        """
        if (request == {}) and all:
            configured_parameters = self._get_configured_parameters(suppress_errors)
            request.update({
                parameter_name: {}
                    for parameter_name, ParameterClass 
                    in configured_parameters.items()
                    if ParameterClass.autostart
                })
        response = {}
        for parameter_name, additional_config in request.items():
            try:
                parameter_response = self._initialize_parameter(parameter_name, additional_config)
                response.update({parameter_name: parameter_response})
            except:
                if not suppress_errors:
                    raise
        return response
    
    def _initialize_parameter(self, name, config):
        """ handle initialization of a single parameter 

        Args:
            (str) name: for non-generic parameter, points to location of 
                ParameterClass definition inside conductor.parameter_directory.
            (dict) config: (key, value) pairs to be set as attributes of class
                instance. additionally, if config.get('generic') == True,
                we will create a generic parameter instead of looking for 
                definition inside conductor.parameter_directory.
        Returns:
            response of parameter's initialization method
        Raises:
            ParameterAlreadyActive: if parameter is already running, we do not
                initialize another instance.
            ParameterInitializationError: if we catch some generic error in the 
                loading or initialization process.
        """
        response = None
        if name in self.parameters:
            raise ParameterAlreadyActiveError(name)
        if config.get('generic'):
            response = self._initialize_generic_parameter(name, config) 
        else:
            response = self._initialize_configured_parameter(name, config)
        return response

    def _initialize_configured_parameter(self, name, config):
        """ initialize a configured parameter """
        try:
            ParameterClass = self._import_parameter(name)
            ParameterClass.server = self
            ParameterClass.servername = self.name
            parameter = ParameterClass()
            parameter._initialize(config)
            self.parameters[name] = parameter
        except ParameterInitializationError:
            raise
        except:
            traceback.print_exc()
            raise ParameterInitializationError(name)

    def _initialize_generic_parameter(self, name, config):
        """ initialize a generic parameter """
        try:
            try:
                value = self._load_parameter_value(name)
            except ParameterValueNotFoundError:
                value = None
            ParameterClass = self._create_generic_parameter(name)
            parameter = ParameterClass()
            parameter._initialize(config)
            parameter.set_value(value)
            self.parameters[name] = parameter
        except ParameterInitializationError:
            raise
        except:
            traceback.print_exc()
            raise ParameterInitializationError(name)

    @setting(3, request_json='s', all='b')
    def terminate_parameters(self, c, request_json='{}', all=False):
        """ terminate parameters specified in the request 
        
        This method makes the private method "_terminate_parameters" available
        over labrad. Look at that method's documentation for exactly how 
        the parameters are terminated.
        
        Args:
            (str) request_json: A json dumped dict specifying
                {parameter_name: None}
            (bool) all: if True, terminate all active parameters

        Returns:
            (str) json dumped dict 
                {<(str) parameter_name>: <termination_response>}
        """
        request = json.loads(request_json)
        response = self._terminate_parameters(request, all)
        self._send_update({'terminate_parameters': response})
        response_json = json.dumps(response, default=lambda x: None)
        return response_json
    
    def _terminate_parameters(self, request={}, all=False, 
                              suppress_errors=False):
        """ terminate parameters specified in the request.
        
        Args:
            (dict) request: keys specify names of parameters to be terminated.
            (bool) all: if True, all active parameters will be terminated.
        Returns:
            (dict) {<(str) parameter_name>: <termination_response>}
                where termination_response is the returned value of 
                <parameter>.terminate()
        """
        if all:
            active_parameters = self._get_active_parameters()
            request = {
                parameter_name: {}
                    for parameter_name, ParameterClass 
                    in active_parameters.items()
                }
        response = {}
        for parameter_name, _ in request.items():
            try:
                parameter_response = self._terminate_parameter(parameter_name)
                response.update({parameter_name: parameter_response})
            except:
                if not suppress_errors:
                    raise
        return response
   
    def _terminate_parameter(self, name):
        """ handle termination of a single parameter 

        Args:
            (str) name: name of parameter to be terminated.
        Returns:
            response of parameter's termination method
        Raises:
            ParameterNotActiveError: cannot terminate a parameter if it is not active.
            ParameterTerminationError: raised if we catch some generic error in 
                the termination process.
        """
        response = None
        if name not in self.parameters:
            raise ParameterNotActiveError(name)
        try:
            parameter = self._get_parameter(name)
            response = parameter._terminate()
            del self.parameters[name]
        except ParameterTerminationError:
            del self.parameters[name]
            raise
        except:
            del self.parameters[name]
            raise ParameterTerminationError(name)
        return response
    
    @setting(4, request_json='s', all='b')
    def reload_parameters(self, c, request_json='{}', all=False):
        """ reload parameters specified in the request 
        
        This method makes the private method "_reload_parameters" available
        over labrad. Look at that method's documentation for exactly how 
        the parameters are reloaded.
        
        Args:
            (str) request_json: A json dumped dict specifying
                {parameter_name: None}
            (bool) all: if True, reload all active parameters

        Returns:
            (str) json dumped dict 
                {<(str) parameter_name>: <reload_response>}
        """
        request = json.loads(request_json)
        response = self._reload_parameters(request, all)
        self._send_update({'reload_parameters': response})
        response_json = json.dumps(response, default=lambda x: None)
        return response_json
    
    def _reload_parameters(self, request={}, all=False):
        """ reload parameters specified in the request.

        Args:
            (dict) request: {<(str) parameter_name>: <(dict) parameter_config>}
                specifies names of parameters to be reloaded and config to be 
                passed to <parameter>.initialize
            (bool) all: if True, all active parameters will be reloaded.
        Returns:
            (dict) {<(str) parameter_name>: <reload_response>}
                where reload_response is the returned value of 
                <parameter>.reload(config)
        """
        if all:
            active_parameters = self._get_active_parameters()
            request = {
                parameter_name: {}
                    for parameter_name, ParameterClass 
                    in active_parameters.items()
                }
        response = {}
        for parameter_name, parameter_config in request.items():
            parameter_response = self._reload_parameter(parameter_name, parameter_config)
            response.update({parameter_name: parameter_response})
        return response
   
    def _reload_parameter(self, name, config):
        """ handle termination of a single parameter 

        Args:
            (str) name: name of parameter to be reloaded.
            (dict) config: (key, value) pairs to be set as attributes of class
                instance.
        Returns:
            response of parameter's initialize method.
        """
        response = None
        try:
            self._terminate_parameter(name)
        except ParameterNotActiveError:
            pass
        self._initialize_parameter(name, config)
        return response
    
    @setting(5)
    def set_parameter_values(self, c, request_json='{}'):
        """ set parameter values specified in the request 
        
        This method makes the private method "_set_parameter_values" available
        over labrad. Look at that method's documentation for exactly how 
        the parameter values are set
        
        Args:
            (str) request_json: A json dumped dict specifying
                {<(str) parameter_name>: <parameter_value>}

        Returns:
            (str) json dumped dict 
                {<(str) parameter_name>: <set_value_response>}
        """
        request = json.loads(request_json)
        response = self._set_parameter_values(request)
        self._send_update({'set_parameter_values': response})
        response_json = json.dumps(response, default=lambda x: None)
        return response_json
    
    def _set_parameter_values(self, request={}):
        """ set parameter values specified in the request.

        Args:
            (dict) request: {<(str) parameter_name>: <parameter_value>}
        Returns:
            (dict) {<(str) parameter_name>: <set_value_response>}
        """
        response = {}
        for parameter_name, parameter_value in request.items():
            parameter_response = self._set_parameter_value(parameter_name, parameter_value)
            response.update({parameter_name: parameter_response})
        return response
    
    def _set_parameter_value(self, name, value):
        """ handle setting value of a single parameter 

        Args:
            (str) name: name of parameter value to be set
            (?) value: can be anything...
        Returns:
            response of parameter's set_value method.
        """
        response = None
        parameter = self._get_parameter(name, initialize=True, generic=True)
        response = parameter._set_value(value)
        return response

    @setting(6, request_json='s', all='b')
    def get_parameter_values(self, c, request_json='{}', all=False):
        """ get parameter values specified in the request 
        
        This method makes the private method "_get_parameter_values" available
        over labrad. Look at that method's documentation for exactly how 
        the parameter values are set
        
        Args:
            (str) request_json: A json dumped dict specifying
                {<(str) parameter_name>: None}
            (bool) all: if True, return all parameter_values.

        Returns:
            (str) json dumped dict 
                {<(str) parameter_name>: <parameter_value>}
        """
        request = json.loads(request_json)
        response = self._get_parameter_values(request, all)
        self._send_update({'get_parameter_values': response})
        response_json = json.dumps(response, default=lambda x: None)
        return response_json 
    
    def _get_parameter_values(self, request={}, all=True):
        """ get parameter values specified in the request.

        Args:
            (dict) request: {<(str) parameter_name>: None}
        Returns:
            (dict) {<(str) parameter_name>: <parameter_value>}
        """
        if (request == {}) and all:
            active_parameters = self._get_active_parameters()
            request = {
                parameter_name: None
                    for parameter_name, ParameterClass 
                    in active_parameters.items()
                }
        response = {}
        for parameter_name in request:
            parameter_value = self._get_parameter_value(parameter_name)
            response.update({parameter_name: parameter_value})
        return response
            
    def _get_parameter_value(self, name):
        """ handle getting value of a single parameter 

        Args:
            (str) name: name of parameter value to be got.
        Returns:
            response of parameter's get_value method.
        Raises:
            ParameterGetValueError: raised if we catch some generic error in 
                the get_value process.
        """
        value = None
        try:
            _ti = time.time()
            parameter = self._get_parameter(name, initialize=True, generic=True)
            value = parameter._get_value()
            _tf = time.time()
            if (_tf - _ti > 0.001) and self.verbose:
                print name, _tf - _ti
            # test if we will be able to flatten to json
#            value_json = json.dumps({name: value})
        except:
            raise ParameterGetValueError(name)
        return value
    
    @setting(106, request_json='s', all='b')
    def get_next_parameter_values(self, c, request_json='{}', all=False):
        """ get next parameter values specified in the request 
        
        This method makes the private method "_get_next_parameter_values" available
        over labrad. Look at that method's documentation for exactly how 
        the parameter values are set
        
        Args:
            (str) request_json: A json dumped dict specifying
                {<(str) parameter_name>: None}
            (bool) all: if True, return all next_parameter_values.

        Returns:
            (str) json dumped dict 
                {<(str) parameter_name>: <next_parameter_value>}
        """
        request = json.loads(request_json)
        response = self._get_next_parameter_values(request, all)
        self._send_update({'get_next_parameter_values': response})
        response_json = json.dumps(response, default=lambda x: None)
        return response_json 
    
    def _get_next_parameter_values(self, request={}, all=True):
        """ get next parameter values specified in the request.

        Args:
            (dict) request: {<(str) parameter_name>: None}
        Returns:
            (dict) {<(str) parameter_name>: <next_parameter_value>}
        """
        if (request == {}) and all:
            active_parameters = self._get_active_parameters()
            request = {
                parameter_name: None
                    for parameter_name, ParameterClass 
                    in active_parameters.items()
                }
        response = {}
        for parameter_name in request:
            next_parameter_value = self._get_next_parameter_value(parameter_name)
            response.update({parameter_name: next_parameter_value})
        return response
            
    def _get_next_parameter_value(self, name):
        """ handle getting next value of a single parameter 

        Args:
            (str) name: name of parameter next_value to be got.
        Returns:
            response of parameter's get_next_value method.
        Raises:
            ParameterGetValueError: raised if we catch some generic error in 
                the get_value process.
        """
        value = None
        try:
            parameter = self._get_parameter(name, initialize=True, generic=True)
            value = parameter._get_next_value()
            # test if we will be able to flatten to json
            value_json = json.dumps({name: value})
        except:
            raise ParameterGetValueError(name)
        return value

    def _advance_parameter_values(self, suppress_errors=False):
        """ advance values in each parameter's value_queue 
        
        Args: 
            None
        Returns:
            None
        """
        active_parameters = self._get_active_parameters().keys()
        ti = time.time()
        for parameter_name in active_parameters:
            try:
                _ti = time.time()
                self._advance_parameter_value(parameter_name)
                _tf = time.time()
                if (_tf - _ti > 0.01) and self.verbose:
                    print parameter_name, _tf - _ti
            except:
                traceback.print_exc()
                if not suppress_errors:
                    raise
        if self.verbose:
            print "advanced parameter values in {} s".format(time.time() - ti)
    
    def _advance_parameter_value(self, name):
        """ advance values in specified parameter's value_queue 
        
        if there is an active conductor.experiment with loop = True,
        the new parameter values will be appended to the end of the value queue.

        Args:
            (str) name: name of parameter to advance
        Returns:
            None
        Raises:
            ParameterAdvanceError: raised if we catch some generic error in 
                the advance process.
        """
        loop = self.experiment.get('loop', False)
        try:
            parameter = self._get_parameter(name)
            parameter._advance(loop)
        except ParameterNotActiveError:
            return
        except:
            traceback.print_exc()
            raise

    
    def _update_parameters(self, suppress_errors=False):
        """ call each parameter's update method 

        the order in which the updates are called is determined by each 
        parameter's <parameter>.priority, with higher priorities being called 
        first.

        Args: 
            None
        Returns:
            None
        """
        ti = time.time()
        for parameter_name in sort_by_priority(self.parameters):
            try:
                self._update_parameter(parameter_name)
            except:
                if not suppress_errors:
                    raise
        if self.verbose:
            print 'updated parameters in {} s'.format(time.time() - ti)

    def _update_parameter(self, name):
        """ call a specified parameter's update method
       
        a parameter's update can be called in a separate thread if the attribute
        <parameter>.call_in_thread is set to true.

        Args:
            (str) name: name of parameter to update
        Returns:
            None
        Raises:
            ParameterUpdateError: raised if we catch some generic error in 
                the update process.
        """
        ti = time.time()
        try:
            parameter = self._get_parameter(name)
        except ParameterNotActiveError:
            return
        except:
            raise
        if parameter.call_in_thread:
            reactor.callInThread(parameter.update)
        else:
            try:
                parameter.update()
            except:
                traceback.print_exc()
                raise ParameterUpdateError(name)
        tf = time.time()

        if self.verbose or parameter.verbose:
            print 'parameter ({}) updated in {} s'.format(parameter.name, tf - ti)

    @setting(7, experiment_json='s', run_next='b')
    def queue_experiment(self, c, experiment_json='{}', run_next=False):
        """ place an experiment in the experiment_queue.

        This method makes the private method "_queue_experiment" available
        over labrad.
        
        Args:
            (str) experiment_json: json dumped dict specifying experiment.
            (bool) run_next: if True, experiment is placed at front of queue,
                otherwise sent to back.

        Returns:
            None
        """

        experiment = json.loads(experiment_json)
        self._queue_experiment(experiment, run_next)

    def _queue_experiment(self, experiment, run_next=False):
        """ place an experiment in the experiment_queue.
        
        Args:
            (str) experiment_json: json dumped dict specifying experiment.
                {
                    "name": (str) experiment_name
                    "parameters": (dict) passed to
                        conductor._initialize_parameters and 
                        conductor._reload_parameters at start of experiment.
                    "parameter_values": (dict) passed to 
                        conductor._set_parameter_values at start of experiment.
                    "loop": (bool) loop parameter_values indefinitely.
                    "repeat_shot": (bool) prevent advance on next shot of 
                        experiment. This will then be overwritten to False.
                }
            (bool) run_next: if True, experiment is placed at front of queue,
                otherwise sent to back.
        Returns:
            None
        """
        if run_next:
            self.experiment_queue.appendleft(experiment)
        else:
            self.experiment_queue.append(experiment)
    
    @setting(8)
    def clear_experiment_queue(self, c):
        self._clear_experiment_queue()
    
    def _clear_experiment_queue(self):
        self.experiment_queue = deque([])
    
    @setting(9)
    def stop_experiment(self, c):
        self._stop_experiment()

    def _stop_experiment(self):
        self.experiment = {}

    def _advance_experiment(self):
        """ pop experiment from queue """
        if len(self.experiment_queue):
            try:
                experiment = {
                    'name': 'unnamed',
                    'parameters': {},
                    'parameter_values': {},
                    'loop': False,
                    'repeat_shot': False,
                    'experiment_number': 0,
                    'shot_number': 0,
                    }
                experiment.update(self.experiment_queue.popleft())
                self.experiment = experiment
                self._fix_experiment_name()
                
                print experiment['parameters']
                self._reload_parameters(experiment['parameters'])
                self._set_parameter_values(experiment['parameter_values'])
                print "experiment ({}): loaded from queue".format(experiment['name'])
                self._log_experiment_number()
            except:
                raise ExperimentAdvanceError()
        else:
            self.experiment = {}
    
    @setting(10)
    def advance(self, c, suppress_errors=False):
        self._advance(suppress_errors)
    
    def _advance(self, suppress_errors=False):
        print time.time()
        # prevent multiple advances from happening at the same time
        if self.is_advancing:
            raise AlreadyAdvancing()
        try:
            # start timer 
            ti = time.time()
            # signal that we are advancing
            self.is_advancing = True
            
            # check status of current experiment
            # if it is comple
            if self.experiment:
                remaining_points = get_remaining_points(self.parameters)
                if remaining_points:
                    if self.experiment.get('shot_number') is not None:
                        self.experiment['shot_number'] += 1
                else:
                    if self.experiment.get('name'):
                        print "experiment ({}): completed".format(self.experiment['name'])
                    self._advance_experiment()
            else:
                self._advance_experiment()

            remaining_points = get_remaining_points(self.parameters)
            if remaining_points:
                if self.experiment.get('repeat_shot'):
                    self.experiment['repeat_shot'] = False
                    remaining_points += 1
                else:
                    self._advance_parameter_values(suppress_errors=suppress_errors)
                #print "experiment ({}): remaining points: {}".format(self.experiment['name'], remaining_points)
                name = self.experiment.get('name')
                shot_number = self.experiment.get('shot_number')
                if self.experiment.get('loop'):
                    print "experiment ({}): shot {}".format(name, shot_number + 1)
                elif (shot_number is not None):
                    print "experiment ({}): shot {} of {}".format(name, 
                            shot_number + 1, remaining_points + shot_number)
            else:
                self._advance_parameter_values(suppress_errors=suppress_errors)
            self._update_parameters(suppress_errors=suppress_errors)
            tf = time.time()
            if self.verbose:
                print 'advanced in {} s'.format(tf - ti)
        except:
            if not suppress_errors:
                raise
        finally:
            self.is_advancing = False
    
    def _get_parameter(self, name, initialize=False, generic=False):
        active_parameters = self._get_active_parameters()
        if name not in active_parameters:
            if initialize:
                configured_parameters = self._get_configured_parameters()
                if name not in configured_parameters:
                    self._initialize_parameter(name, {'generic': generic})
                else:
                    self._initialize_parameter(name, {})
            else:
                raise ParameterNotActiveError(name)

        return self.parameters[name]
    
    def _import_parameter(self, parameter_name, suppress_errors=False):
        module_path = '{}.parameters.{}'.format(self.name, parameter_name)
        parameter_class_name = 'Parameter'
        try:
            module = importlib.import_module(module_path)
            reload(module)
            if hasattr(module, parameter_class_name):
                ParameterClass = getattr(module, parameter_class_name)
                ParameterClass.name = parameter_name
                return ParameterClass
            else:
                return None
        except ImportError as e:
            module_name = module_path.split('.')[-1]
            if str(e) == 'No module named {}'.format(module_name):
                traceback.print_exc()
                if not suppress_errors:
                    raise ParameterNotFoundError(parameter_name)
            traceback.print_exc()
            if not suppress_errors:
                raise ParameterImportError(parameter_name)
        except:
            traceback.print_exc()
            if not suppress_errors:
                raise ParameterImportError(parameter_name)
    
    def _create_generic_parameter(self, parameter_name):
        class GenericParameterClass(ConductorParameter):
            name = parameter_name
        return GenericParameterClass

    def _load_parameter_values(self):
        values_filename = os.path.join('.values', 'current.json')
        values_path = os.path.join(self.parameter_directory, values_filename)
        if os.path.exists(values_path):
            with open(values_path, 'r') as infile:
                values = json.load(infile)
            return values
        else:
            return {}
    
    def _load_parameter_value(self, parameter_name):
        values = self._load_parameter_values()
        if parameter_name not in values:
            raise ParameterValueNotFoundError(parameter_name)
        else:
            return values.get(parameter_name)
    
    def _save_parameter_values(self):
        old_values = self._load_parameter_values()
        new_values = self._get_parameter_values(request={}, all=True)
        save_values = {}
        save_values.update(old_values)
        save_values.update(new_values)
        
        values_filename = os.path.join('.values', 'current.json')
        values_path = os.path.join(self.parameter_directory, values_filename)
        with open(values_path, 'w') as outfile:
            json.dump(save_values, outfile)
        
        values_filename = os.path.join('.values', '{}.json'.format(time.strftime('%Y%m%d')))
        values_path = os.path.join(self.parameter_directory, values_filename)
        with open(values_path, 'w') as outfile:
            json.dump(save_values, outfile)

    def _fix_experiment_name(self):
        time_string = time.strftime('%Y%m%d')
        name = self.experiment.get('name')
        log_directory = os.path.join(self.experiment_directory, time_string)
        glob_pathname = os.path.join(log_directory, name + '#*')
        previous_experiments = [x for x in glob.glob(glob_pathname)]
        previous_experiment_numbers = [int(pathname.split('#')[-1]) for pathname in previous_experiments]
        if previous_experiment_numbers:
            experiment_number = max(previous_experiment_numbers) + 1
        else:
            experiment_number = 0
        self.experiment['experiment_number'] = experiment_number
        self.experiment['name'] = os.path.join(time_string, '{}#{}'.format(name, experiment_number))

    def _log_experiment_number(self):
        log_path = os.path.join(self.experiment_directory, self.experiment.get('name'))
        log_dir, log_name = os.path.split(log_path)
        if not os.path.isdir(log_dir):
            os.makedirs(log_dir)
        open(log_path, 'a').close()

    def _send_update(self, update):
        update_json = json.dumps(update, default=lambda x: None)
        self.update(update_json)
    
Server = ConductorServer

if __name__ == "__main__":
    from labrad import util
    reactor.suggestThreadPoolSize(5)
    util.runServer(Server())
