from labrad.server import setting
from server_tools.threaded_server import ThreadedServer
import json
import time

class InfluxDBUploader(ThreadedServer):
    name = "influxdb_uploader_server"

    ALLOWED_TYPES_INFLUXDB = (bool, int, float, str) # allowed type of influxdb field value

    def initServer(self):
        pass

    @setting(1, exp_rel_path='s', shot_num_str='s', parameters_json='s')
    def upload_conductor_parameters(self, c, exp_rel_path, shot_num_str, parameters_json):
        print(parameters_json)
        # experiment_name = experiment_rel_path.split("warmup_")[1].split('#')[0]
        # parameters = json.loads(parameters_json)

Server = InfluxDBUploader

if __name__ == "__main__":
    from labrad import util
    util.runServer(Server())


