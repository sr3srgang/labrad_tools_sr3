from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

# Database credentials
token = "yelabtoken"
org = "yelab"
bucket = "sr3"  # Ensure the bucket exists in your database UI.
url = "http://yemonitor.colorado.edu:8086"

def write_influxdb(name,value):
    """
    Update InfluxDB with a single value and a name.

    :param value: The value to write to the database.
    :param name: The name associated with the value.
    """
    with InfluxDBClient(url=url, token=token, org=org) as client:
        write_api = client.write_api(write_options=SYNCHRONOUS)
        
        # Format the data for the database server
        message = f"live_data,host=myhost {name}={value}"
        
        write_api.write(bucket, org, message)
        
        # print(message)  # Print to the console

# # Example usage:
# update_influxdb(0.1, 'mot_fluro')
