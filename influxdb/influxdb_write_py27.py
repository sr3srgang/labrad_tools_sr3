import requests

# Database credentials
token = "yelabtoken"
org = "yelab"
bucket = "sr3"  # Ensure the bucket exists in your database UI.
url = "http://yemonitor.colorado.edu:8086"

# Convert record (JSON or dict-style data) to Line Protocol
def record_to_line_protocol(record):
    measurement = record["measurement"]
    tags = ",".join(["{}={}".format(k.replace(" ", "\\ "), v.replace(" ", "\\ ")) for k, v in record.get("tags", {}).items()])
    fields = ",".join(["{}={}".format(k.replace(" ", "\\ "), v) for k, v in record["fields"].items()])
    return "{},{} {}".format(measurement, tags, fields)

# Convert list of records to Line Protocol
def records_to_line_protocol(records):
    return "\n".join([record_to_line_protocol(r) for r in records])


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
    # convert records to line data
    line_protocol_data = records_to_line_protocol(records)
    
    # Write URL
    write_url = "{}/api/v2/write?org={}&bucket={}&precision=s".format(url, org, bucket)

    # Headers
    headers = {
        "Authorization": "Token {}".format(token),
        "Content-Type": "text/plain; charset=utf-8"
    }
    
    # Send data
    response = requests.post(write_url, headers=headers, data=line_protocol_data)
    return response

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
    
    return write_influxdb_records(records)



def write_influxdb(name,value):
    """
    Update InfluxDB with a single value and a name.

    :param value: The value to write to the database.
    :param name: The name associated with the value.
    """
    fields = {name: value}
    
    return write_influxdb_fields(fields)


# test code to run
if __name__ == "__main__":
    # JSON-style test data
    records = [
        {
            "measurement": "test_measurement",
            "tags": {
                "test_tag": "test_value",
            },
            "fields": {
                "test_field": 1.5,
                },
        }
    ]
    
    # send test data and get the response
    response = write_influxdb_records(records)
    
    # Check response
    if response.status_code == 204:
        print("Write successful")
    else:
        print("Error:", response.text)
    
