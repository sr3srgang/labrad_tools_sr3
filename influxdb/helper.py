"""
Constants, variables, and helper functions for InfluxDB uploader
"""

import traceback

ALLOWED_FIELD_VALUE_TYPES_INFLUXDB = (bool, int, float, str) # allowed type of influxdb field value

INFLUXDB_UPLOADER_SERVER_NAME = "influxdb_uploader_server"
INFLUXDB_GET_EXPERIMENT_METHOD_NAME = "get_current_experiment_info"
INFLUXDB_UPLOAD_METHOD_NAME = "upload_experiment_shot"
INFLUXDB_UPLOADER_TIMEOUT = 2 # seconds

def validate_influxdb_uploader(cxn):
    """
    Check if the InfluxDB uploader server and methods are available and
    return the availability.
    """
    # # if alabrad client is not given as argument, create one and return it
    # if cxn is None:
    #     cxn = labrad.connect()
    is_available = False
    uploader_server = None
    get_current_experiment_info = None
    upload_experiment_shot = None
    try:
        # print(f"[DEBUG] cxn = {cxn} ({type(cxn)})")
        # print(f"[DEBUG] cxn.cxn = {cxn.cxn} ({type(cxn.cxn)})")
        uploader_server = getattr(cxn, INFLUXDB_UPLOADER_SERVER_NAME, None)
        if uploader_server is None:
            raise AttributeError(f"`{INFLUXDB_UPLOADER_SERVER_NAME}` server is not found. Check if the server is running.")
        get_current_experiment_info = getattr(uploader_server,INFLUXDB_GET_EXPERIMENT_METHOD_NAME, None)
        if get_current_experiment_info is None:
            raise AttributeError(f"`{INFLUXDB_GET_EXPERIMENT_METHOD_NAME}()` method in `{INFLUXDB_GET_EXPERIMENT_METHOD_NAME}` server is not found. Check if the server is running.")
        upload_experiment_shot = getattr(uploader_server, INFLUXDB_UPLOAD_METHOD_NAME, None)
        if upload_experiment_shot is None:
            raise AttributeError(f"`{INFLUXDB_UPLOAD_METHOD_NAME}()` method in `{INFLUXDB_GET_EXPERIMENT_METHOD_NAME}` server is not found. Check if the server is running.")
        is_available = True
    except:
        print("[WARN] Failed to connection to influxDB.")
        traceback.print_exc()
        print()
        
    # print(f"[DEBUG] InfluxDB uploader server is available: {is_available}\n"
    #         f"[DEBUG] \tuploader_server = {uploader_server}\n"
    #         f"[DEBUG] \tget_current_experiment_info = {get_current_experiment_info}\n"
    #         f"[DEBUG] \tupload_experiment_shot = {upload_experiment_shot}\n")
    return is_available, uploader_server, get_current_experiment_info, upload_experiment_shot
