from labrad.server import setting
from server_tools.threaded_server import ThreadedServer
import json
import time
from influxdb_write import write_influxdb_records, ALLOWED_FIELD_VALUE_TYPES_INFLUXDB
from pprint import pprint, pformat
from datetime import datetime



class InfluxDBUploader(ThreadedServer):
    name = "influxdb_uploader_server"

    DEBUG_MODE = False
    # DEBUG_MODE = True
    def print_debug(self, msg):
        if self.DEBUG_MODE is not True:
            return
        print(f"[DEBUG] {str(msg)}\n\tfrom {__file__}")

    def initServer(self):
        pass

    @setting(1, exp_rel_path='s', shot_num='i', parameters_json='s')
    def upload_conductor_parameters(self, c, exp_rel_path, shot_num, parameters_json):
        self.print_debug('upload_conductor_parameters() called.')
        print(f'Received conductor parameters for {exp_rel_path}.')
        self.print_debug(f"exp_rel_path={exp_rel_path}, shot_num={shot_num}")
        # self.print_debug(f'Received conductor parameters:\n{pformat(parameters_json)}')
        
        # process arguments
        parameters = json.loads(parameters_json)
        self.print_debug(f"parameters=\n{pformat(parameters)}")
        
        timestamp = parameters["timestamp"]
        exp_dt = datetime.fromtimestamp(timestamp)
        exp_path = exp_rel_path
        exp_type, exp_num = exp_rel_path.split("warmup_")[1].split("#")
        exp_num = int(exp_num)
        # shot_num = shot_num
        
        self.print_debug(f"\texp_type={exp_type}, shot_num={exp_num} at {timestamp} ({exp_dt:%Y-%m-%d %H:%M:%S:%f})")
        # TBD for timestamp print_debug (local & Z)
        
        # Form InfluxDB record to upload
        # IT IS IMPORTANT to give a unique `source` tag or the record will overide the previous record in the db with the same `tags`.
        record = {
            "measurement": "labrad_upload_server",
            "tags": { 
                    "source" : "upload_conductor_parameters@labrad_upload_server", # GIVE UNIQUE SOURCE NAME per upload with the same `tags`!
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
        
        # TBD
        # self.print_debug(f"")
        
        # select the parameters which value has an allowed type for influxdb field values 
        parameters_upload = {}
        for name, value in parameters.items():
            if isinstance(name, str) is False:
                continue
            if isinstance(value, ALLOWED_FIELD_VALUE_TYPES_INFLUXDB) is False:
                continue
            if isinstance(value, (int,float)):
                value = float(value)
            parameters_upload[name] = value
        # parameters_upload["sequencer.lat_top_clock"] = parameters["sequencer.lat_top_clock"]
            
        # TBD
        self.print_debug(f"parameters_upload=\n{pformat(parameters_upload)}")
                    
        # add the selected parameters in record to upload
        record["fields"].update(parameters_upload)
        
        # upload to influxdb
        records = [record]
        write_influxdb_records(records)
        
        print("Uploaded to InfluxDB\n")

Server = InfluxDBUploader


if __name__ == "__main__":
    from labrad import util
    util.runServer(Server())





