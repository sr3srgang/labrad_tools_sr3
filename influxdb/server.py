from labrad.server import setting
from server_tools.threaded_server import ThreadedServer
import json

import sys
import time
from datetime import datetime, timezone

from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

from pprint import pprint, pformat

def print_error(self, msg):
    print(msg, file=sys.stderr)

ALLOWED_FIELD_VALUE_TYPES_INFLUXDB = (bool, int, float, str) # allowed type of influxdb field value

class InfluxDBUploader(ThreadedServer):
    name = "influxdb_uploader_server"
    
    INFLUXDB_URL = "http://yemonitor.colorado.edu:8086"
    INFLUXDB_TOKEN = "yelabtoken"
    INFLUXDB_ORG = "yelab"
    INFLUXDB_BUCKET = "sr3"  # Ensure the bucket exists in your database UI.

    DEBUG_MODE = False
    # DEBUG_MODE = True
    def print_debug(self, msg):
        if self.DEBUG_MODE is not True:
            return
        print(f"[DEBUG] {str(msg)}\n\tfrom {__file__}")


    # >>>>>>> LabradServer methods >>>>>>>
    
    def __init__(self):
        # essentially inherited LabradServers's __init__ method; no need to modify it.
        # In particular, the object already has Labrad client `self.cxn` defined.
        super(InfluxDBUploader, self).__init__()
    
    def initServer(self):
        """overidding initServer() placeholder in LabradServer"""
        pass
    
    def stopServer(self):
        """overidding stopServer() placeholder in LabradServer"""
        pass
    
    # <<<<<<< LabradServer methods <<<<<<<
    
    
    
    
    # >>>>>>> InfluxDB upload methods >>>>>>>
    
    # >>>>> General InfluxDB upload >>>>>
    def _verify_influxdb_records(self, records):
        """Verify the records to be uploaded to InfluxDB."""
        for record in records:
            # check required record keys exist
            if isinstance(record, dict) is False:
                raise TypeError("record must be a dictionary")
            if "measurement" not in record:
                raise KeyError("record must contain 'measurement' key")
            if "tags" not in record:
                raise KeyError("record must contain 'tags' key")
            if "fields" not in record:
                raise KeyError("record must contain 'fields' key")
            # timestamp is optional
            # if "timestamp" not in record:
            #     raise KeyError("record must contain 'timestamp' key")
            
            # check required record keys are of the correct type
            if isinstance(record["measurement"], str) is False:
                raise TypeError("measurement must be a string")
            if isinstance(record["tags"], dict) is False:
                raise TypeError("tags must be a dictionary")
            if isinstance(record["fields"], dict) is False:
                raise TypeError("fields must be a dictionary")
            if "timestamp" in record:
                if isinstance(record["timestamp"], (int, datetime)) is False:
                    raise TypeError("timestamp must have float or datetime types.")
            
            # check fields are valid for influxdb
            for name, value in record["fields"].items():
                if isinstance(name, str) is False:
                    raise TypeError("field name must be a string")
                if isinstance(value, ALLOWED_FIELD_VALUE_TYPES_INFLUXDB) is False:
                    raise TypeError(f"field value must be one of {ALLOWED_FIELD_VALUE_TYPES_INFLUXDB}")
                
            # check if tags are valid for influxdb
            for name, value in record["tags"].items():
                if isinstance(name, str) is False:
                    raise TypeError("tag name must be a string")
                if isinstance(value, str) is False:
                    raise TypeError("tag value must be a string")
    
    def _upload(self, records):
        """
        The most general method for InfluxDB upload.
        Upload "records" to Sr3 bucket in yemonitor InfluxDB.
        
        "records" is a list of "record"s.
        "record" is a set of data with the associated timestamp; simply a data point at a time.
        "record" is given as a dictionary like below:
        record = {   
            "measurement": "live_data",
                "tags": { 
                    "host": "myhost",
                    },
                "fields": {
                    "<name1>": <value1>,
                    "<name2>": <value2>,
                    },
        }
        
        :param records: A record or a list of records to upload. Each record is a dictionary.
        """
        if isinstance(records, list) is False:
            records = [records]
            
        self._verify_influxdb_records(records)
            
        with InfluxDBClient(url=self.INFLUXDB_URL, token=self.INFLUXDB_TOKEN, org=self.INFLUXDB_ORG) as client:
            with client.write_api(write_options=SYNCHRONOUS) as writer:
                writer.write(bucket=self.INFLUXDB_BUCKET, record=records)
                
        print("Uploaded to InfluxDB")
        print()
    
    @setting(1, records_json='s')
    def upload(self, c, records_json):
        """
        LabRAD-server method wrapper of _upload() method
        Refer to the doctring of _upload() method for details.
        
        wrapper-specific arguments:
        :param records_json: The JSON-serialized records to upload.
        """
        self.print_debug('upload() called.')
        records = json.loads(records_json)
        self.print_debug(f"Received & parsed records: {pformat(records)}")
        
        # upload the records to InfluxDB
        self._upload(records)
    
    # <<<<< General InfluxDB upload <<<<<
    
    
    
    # >>>>> Upload for a RossRAD experiment shot >>>>> 
        
    def _upload_experiment_shot(self, exp_rel_path, shot_num, timestamp, uploaded_from, 
                     fields, tags = {}, measurement = "labrad_upload_server"):
        """
        Upload a record associated to a single RossRAD experiment shot to InfluxDB.
        
        IT IS IMPORTANT to give a unique `measurement`, `uploaded_from`, and `tags` below or 
        the record will overide the previous record in the db for the shot.
        
        :param exp_rel_path: The relative path of the experiment to be got from conductor server.
        :param shot_num: The shot number to be got from conductor server.
        :param timestamp: The timestamp of the experiment to be got from conductor server.
        :param uploaded_from: The source of the upload.
                            Intended use: the name of function, method@class, script file name, etc
                            that calls this method or the server method wrapper for this method.
        :param fields: The fields (i.e. data) to upload.
        :param tags: The tags (i.e. metadata) for the record.
        :param measurement: The measurement name in InfluxDB. Default is "labrad_upload_server".
        """
        
        # parse the arguments
        exp_path = exp_rel_path
        exp_type, exp_num = exp_rel_path.split("warmup_")[1].split("#")
        exp_num = int(exp_num)
        timestamp = float(timestamp)
        exp_dt = datetime.fromtimestamp(timestamp)
        
        if self.DEBUG_MODE:
            local_time = exp_dt.strftime("%Y-%m-%d %H:%M:%S:%f %z")
            utc_time = exp_dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S:%f %z")
            self.print_debug(f"\texp_type={exp_type}, shot_num={exp_num} at {timestamp} "
                            f"(local: {local_time}, UTC: {utc_time})")
        
        # record populated with must-have data for experiment shot
        record = {
            "measurement": measurement,
            "tags": { 
                    "uploaded_from" : uploaded_from,
                    "exp_path": exp_path,
                    "exp_type": exp_type,
                    "exp_num": f"{exp_num}",
                    "shot_num": f"{shot_num}",
                },
            "timestamp": exp_dt,  # Ensure timezone awareness
            "fields": {
                    "exp_num": exp_num,
                    "shot_num": shot_num,
                },
        }
        
        # add the fields and tags to the record
        record["fields"].update(fields)
        record["tags"].update(tags)
            
        # upload to InfluxDB
        self._upload(record)
    
    @setting(2, exp_rel_path='s', shot_num='i', timestamp='v', uploaded_from='s',
                   fields_json='s', tags_json="s", measurement='s')
    def upload_experiment_shot(self, c, exp_rel_path, shot_num, timestamp, uploaded_from,
                   fields_json, tags_json, measurement):
        """
        LabRAD-server method wrapper of _upload_experiment_shot() method
        Refer to the doctring of _upload_experiment_shot() method for details.
        
        wrapper-specific arguments:
        :param fields_json: The JSON-serialized fields to upload.
        :param tags: The JSON-serialized tags for the record.
        """
        self.print_debug('upload_shot() called.')
        
        # deserialize the JSON arguments
        fields = json.loads(fields_json)
        tags = json.loads(tags_json)
        
        # print_debug all the arguments
        if self.DEBUG_MODE:
            msg = "Received (and parsed) arguments: "
            msg += f"\n\texp_rel_path={exp_rel_path}"
            msg += f"\n\tshot_num={shot_num}"
            msg += f"\n\ttimestamp={timestamp}"
            msg += f"\n\tuploaded_from={uploaded_from}"
            msg += f"\n\tfields={pformat(fields)}"
            msg += f"tags={pformat(tags)}"
            msg += f"\n\tmeasurement={measurement}"
            self.print_debug(msg)
        
        # upload the shot 
        self._upload_experiment_shot(exp_rel_path, shot_num, timestamp, uploaded_from, 
                                     fields, tags, measurement)
        
    
    # <<<<< Upload for a RossRAD experiment shot <<<<<<<
    
    # >>>>> Upload for conductor parameters >>>>>
    
    def _upload_conductor_parameters(self, exp_rel_path, shot_num, parameters):
        """
        Upload the conductor parameters for a RossRAD experiment shot to InfluxDB.
        
        """
        
        timestamp = parameters["timestamp"]
        
        # Form InfluxDB record to upload
        measurement = "conductor_parameters"
        # IT IS IMPORTANT to give a unique "uploaded_from" and `tags` below or 
        # the record will overide the previous record in the db for the shot.
        uploaded_from = "upload_conductor_parameters@labrad_upload_server"
        tags = {
            "type": "conductor parameter",
        }
        
        # select the parameters which value has an allowed type for influxdb field values 
        parameters_upload = {}
        parameters_skip = {}
        for name, value in parameters.items():
            if isinstance(name, str) is False:
                parameters_skip[name] = value
                continue
            if isinstance(value, ALLOWED_FIELD_VALUE_TYPES_INFLUXDB) is False:
                parameters_skip[name] = value
                continue
            if isinstance(value, (int,float)):
                value = float(value)
            parameters_upload[name] = value
    
        print_error(f"parameters uploaded: {list(parameters_upload.keys())}")
        print_error(f"parameters skipped: {list(parameters_skip.keys())}")
        
        self._upload_experiment_shot(exp_rel_path, shot_num, timestamp, 
                     uploaded_from=uploaded_from,
                     fields=parameters_upload, tags=tags, measurement=measurement)
        
        
        # upload the values from postprocessing conductor parameters
        fields = {}
        
        name = "test"
        if name in parameters:
            value = parameters[name]
            fields[name] = value
            
        if fields:
            tags = {
                "type": "derived from conductor_parameter",
            }
            self._upload_experiment_shot(exp_rel_path, shot_num, timestamp, 
                     uploaded_from=uploaded_from,
                     fields=fields, tags=tags, measurement=measurement)
        
        
        
    # def _postprocess_conductor_parameters(self, exp_rel_path, shot_num, parameters):
    #     """
    #     Return values derived from conductor parameters.
    #     Intended to be used in the upload_conductor_parameters() method.
        
    #     Example usages: 
    #     - Convert the conductor parameter values to a valid types for InfluxDB.
    #     - Select an item with the valid type from the pamater values with a collection type (e.g. list, tuple, dict).
    #     """
        
    #     timestamp = parameters["timestamp"]
        
    #     # Form InfluxDB record to upload
    #     measurement = "postprocessed_conductor_parameters"
    #     # IT IS IMPORTANT to give a unique "uploaded_from" and `tags` below or 
    #     # the record will overide the previous record in the db for the shot.
    #     uploaded_from = "upload_postprocessed_conductor_parameters@labrad_upload_server"
    #     tags = {
    #         "type": "postprocessed_conductor_parameter",
    #     }

        

    @setting(3, exp_rel_path='s', shot_num='i', parameters_json='s')
    def upload_conductor_parameters(self, c, exp_rel_path, shot_num, parameters_json):
        """
        LabRAD-server method wrapper of _upload_conductor_parameters() method
        Refer to the doctring of _upload_conductor_parameters() method for details.
        
        wrapper-specific arguments:
        :param parameters_json: The JSON-serialized conductor parameters to upload.
        """
        self.print_debug('upload_conductor_parameters() called.')
        
        # parse arguments
        parameters = json.loads(parameters_json)
        self.print_debug(f"parameters=\n{pformat(parameters)}")
        
        if self.DEBUG_MODE:
            msg = "Received (and parsed) arguments: "
            msg += f"\n\texp_rel_path={exp_rel_path}"
            msg += f"\n\tshot_num={shot_num}"
            msg += f"\n\tparameters={pformat(parameters)}"
            self.print_debug(msg)
            
        # upload the conductor parameters
        self._upload_conductor_parameters(exp_rel_path, shot_num, parameters)
        

        
    # <<<<< Upload for conductor parameters <<<<<<<       
        
        
        
    # <<<<<<< InfluxDB upload methods <<<<<<<

Server = InfluxDBUploader


if __name__ == "__main__":
    from labrad import util
    print(">>>>>>> InfluxDB uploader LabRAD server >>>>>>>")
    util.runServer(Server())
    print("<<<<<<< InfluxDB uploader LabRAD server <<<<<<<")





