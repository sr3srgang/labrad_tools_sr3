from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
import numpy as np
import json

# Database credentials
token = "yelabtoken"
org = "yelab"
bucket = "sr3"  # Ensure the bucket exists in your database UI.
url = "http://yemonitor.colorado.edu:8086"


# def write_influxdb(name, value):
#     """
#     Update InfluxDB with a single value and a name.

#     :param value: The value to write to the database.
#     :param name: The name associated with the value.
#     """
#     with InfluxDBClient(url=url, token=token, org=org) as client:
#         write_api = client.write_api(write_options=SYNCHRONOUS)

#         # Format the data for the database server
#         message = f"live_data,host=myhost {name}={value}"

#         write_api.write(bucket, org, message)

#         # print(message)  # Print to the console

# # Example usage:
# update_influxdb(0.1, 'mot_fluro')


def write_influxdb(name, value):
    # Database credentials and client setup
    from influxdb_client import InfluxDBClient
    from influxdb_client.client.write_api import SYNCHRONOUS

    token = "yelabtoken"
    org = "yelab"
    bucket = "sr3"
    url = "http://yemonitor.colorado.edu:8086"

    with InfluxDBClient(url=url, token=token, org=org) as client:
        write_api = client.write_api(write_options=SYNCHRONOUS)

        # Check if value is a list or numpy array; if so, convert to a JSON string.
        if isinstance(value, (list, np.ndarray)):
            # If value is a numpy array, convert it to a list first.
            if isinstance(value, np.ndarray):
                value = value.tolist()
            # Convert to JSON string
            value_str = json.dumps(value)
            # Ensure that the string value is enclosed in quotes in the line protocol.
            message = f'live_data,host=myhost {name}="{value_str}"'
        else:
            message = f"live_data,host=myhost {name}={value}"

        write_api.write(bucket, org, message)
        print(message)
