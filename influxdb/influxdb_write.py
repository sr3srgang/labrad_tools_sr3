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
   
      
def write_influxdb_records(records):
    """
    Upload the multiple "record" (a set of data with the associated timestamp; simply a data point at a time) at once
    "record" is given as a dictionary like below
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
    
    Arguments:
     - records: the list of "record" dict
    """
    with InfluxDBClient(url=url, token=token, org=org) as client:
            with client.write_api(write_options=SYNCHRONOUS) as writer:
                writer.write(bucket=bucket, record=records)
        
        
def write_influxdb_fields(fields):
    """
    Upload multiple (name, value) pairs at once
    
    Arguments:
        - fields: dictionary with names as the keys and values as the values
                (e.g., data = {"<name1>": <value1>, "<name2>": <value2>, ...})
    """
    
    records = [{   
        "measurement": "live_data",
            "tags": { "host": "myhost" },
            "fields": fields
    }]
    
    with InfluxDBClient(url=url, token=token, org=org) as client:
            with client.write_api(write_options=SYNCHRONOUS) as writer:
                writer.write(bucket=bucket, record=records)
    

