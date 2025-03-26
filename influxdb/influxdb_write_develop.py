# 2024/11/03 Modified by Joonseok Hur

from typing import TypedDict
from typing import List, Dict, Any, Optional, overload
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

# default influxdb info
influxdb_default_token = "yelabtoken"
influxdb_default_org = "yelab"
# Ensure the bucket exists in your database UI.
influxdb_default_bucket = "sr3"
influxdb_default_url = "http://yemonitor.colorado.edu:8086"


def write_influxdb(name, value):
    """
    Update InfluxDB with a single value and a name.

    :param value: The value to write to the database.
    :param name: The name associated with the value.
    """
    with InfluxDBClient(url=influxdb_default_url, token=influxdb_default_token, org=influxdb_default_org) as client:
        write_api = client.write_api(write_options=SYNCHRONOUS)

        # Format the data for the database server
        message = f"live_data,host=myhost {name}={value}"

        write_api.write(influxdb_default_bucket, influxdb_default_org, message)

        # print(message)  # Print to the console


def write_influxdb_legacy(name, value):
    # input type checks
    if isinstance(name, str) is False:
        raise TypeError("name of datum does not have string type.")
    print("Legacy function is called.")
    pass

# The JSON format of sample data to be uploaded to InfluxDB:
# It is basically a Python list of sample data, each of which has
# the form of Python dict, as below.
# json_body = [
#     {
#         "measurement": <measurement name in str>,
#         "tags": {
#                       <tag key 1 in str>: <tag value 1>,
#                       <tag key 2 in str>: <tag value 2>,
#                       ...
#                  },
#         "time": <str formatted for timestamp>, # can be omitted
#         "fields": {
#                       <field key 1 in str>: <field value 1>},
#                    ...
#                    }
#     },
#     <datum 2>,
#      ...
# ]
# e.g.,
# records = [
#     {
#         "measurement": "TC08logger",
#         "tags": {
#             "Location": "MOT coil cooling pipe in",
#             "LoggerSN": 12345
#         },
#         "time": "2024-10-30T8:01:00Z", # can be omitted
#         "fields": {
#             "Temperature[degC]": 127
#         }
#     },
# ]
# structure of a sample datum
# # timestamp: Optional. The timestamp for the data point. Each sample
# #            has only one timestamp. The server’s local nanosecond
# #            timestamp in UTC is assinged if the timestamp is not included with
# #            the point.
# # measurement: a high-level description of all timestamped data
# #              collected. it only takes str and does not have
# #              key-value pairing unlike tags and fields below.
# #              It can be compared to the title of a table
# # fields: key[str]-value pairs that store actual data value. A key
# #         takes the type of the data (e.g., voltage[V],
# #         frequency[Hz], temperature[degC]) and the associated
# #         value takes the value of the data. A key can be compared
# #         to a main column in a table, to write measurement results,
# #         labeled as the key in the head cell.
# #         The associated values to the key from different timestamped
# #         sample data corresponds to the values in the cells below
# #         the head cell along the column below from the rows for
# #         data measured at different times, respectively. The field
# #         value can take four data types: bool, int, float, and
# #         string. The fields are not indexed or provide fast query,
# #         which should make sense considering the intended use of the
# #         fields. (e.g., it would not be usual to query the sample
# #         data with a particular temperature, say, 10.65 degC.)
# # tags: Optional. key[str]-value pair that records metadata of the
# #       actual data. Each value takes further description, of the same
# #       type described in the key paired with the value, of each
# #       timestamped sample data. (e.g., "JH", "YY", "MT", "MM" values
# #       for "researcher name" key; "breadboard surface", "laser diode
# #       mount", "ambient at room center" values for "measurement
# #       location" key; 1, 2, 3 values for "priority" key.)
# #       A key and associated values can be compared as the header
# #       label and contents in a column for additional descrition of
# #       each measurement. The tags are indexed and therefore provide
# #       fast & efficient queries on a tag value, which is natural
# #       useful. (e.g., when query the data measured by a "researcher
# #       name" "JH" ; or the temperature at the "location" "laser
# #       diode mount".)
#
# Refer to the below for more details on sample data formatting
# Getting Started with Python and InfluxDB; see "Inserting Data" section
# https://www.influxdata.com/blog/getting-started-python-influxdb/
# InfluxDB Python Examples
# https://influxdb-python.readthedocs.io/en/latest/examples.html

# For better understanding of each sample datum's stucture:
# https://docs.influxdata.com/influxdb/v1/concepts/key_concepts/
# https://docs.influxdata.com/influxdb/cloud/reference/key-concepts/data-elements/
# Data types
# https://docs.influxdata.com/influxdb/v1/write_protocols/line_protocol_reference/#data-types
# InfluxDB glossary
# https://docs.influxdata.com/influxdb/v1/concepts/glossary/


@overload
def write_influxdb_new(
    name: str, value: Any
) -> None:
    """ Legacy function for uploading one (name, value) pair to InfluxDB"""
    ...


@overload
def write_influxdb_new(
    measurement: str, name: str, value: Any,
    time: Optional[str] = None,
    *,
    token: str = influxdb_default_token,
    org: str = influxdb_default_org,
    # Ensure the bucket exists in your database UI.
    bucket: str = influxdb_default_bucket,
    url: str = influxdb_default_url
) -> None:
    """ Uploading one (name, value) pair to InfluxDB"""
    ...


@overload
def write_influxdb_new(
    measurement: str, names: List[str], values: List[Any],
    time: Optional[str] = None,
    *,
    token: str = influxdb_default_token,
    org: str = influxdb_default_org,
    # Ensure the bucket exists in your database UI.
    bucket: str = influxdb_default_bucket,
    url: str = influxdb_default_url
) -> None:
    """ Uploading multiple (name, value) pairs to InfluxDB"""
    ...


@overload
def write_influxdb_new(
    *,
    measurement: str = influxdb_default_bucket,
    tags: Optional[Dict[str, Any]] = None,
    time: Optional[str] = None,
    fields: Dict[str, Any],
    token: str = influxdb_default_token,
    org: str = influxdb_default_org,
    # Ensure the bucket exists in your database UI.
    bucket: str = influxdb_default_bucket,
    url: str = influxdb_default_url
) -> None:
    """ Uploading one sample datum to InfluxDB"""
    ...


class InfluxDBDataTypedDict(TypedDict):
    measurement: str
    tags: Optional[Dict[str, Any]]
    time: Optional[str]
    fields: Dict[str, Any]


@overload
def write_influxdb_new(
    records: List[InfluxDBDataTypedDict], *,
    token: str = influxdb_default_token,
    org: str = influxdb_default_org,
    # Ensure the bucket exists in your database UI.
    bucket: str = influxdb_default_bucket,
    url: str = influxdb_default_url
) -> None:
    """ Uploading JSON-formatted sample data to InfluxDB"""
    ...

# functions to compose JSON for influxDB from


def composeInfluxDBDataJSON_singleNameValue(
    measurement: str, name: str, value: Any,
    time: Optional[str] = None,
) -> List[InfluxDBDataTypedDict]:
    # input type checks
    if isinstance(measurement, str) is False:
        raise TypeError("measurement of datum does not have string type.")
    if isinstance(name, str) is False:
        raise TypeError("name of datum does not have string type.")
    if (time is not None) and (isinstance(time, str) is False):
        raise TypeError("Time does not have string type.")

    fields = {name: value}
    record = {}
    record['measurement'] = measurement
    if time is not None:
        record['time'] = time
    record['fields'] = fields
    records = [record]
    return records


def composeInfluxDBDataJSON_multipleNameValues(
    measurement: str, names: List[str], values: List[Any],
    time: Optional[str] = None
) -> List[InfluxDBDataTypedDict]:
    # input type checks
    if isinstance(measurement, str) is False:
        raise TypeError("measurement of datum does not have string type.")
    if len(names) != len(values):
        raise TypeError("name and value lists have different lengths.")
    if all([isinstance(name, str) for name in names]) is False:
        raise TypeError(
            "A name in name list does not have string type.")
    if (time is not None) and (isinstance(time, str) is False):
        raise TypeError("Time does not have string type.")

    fields = {name: value for name, value in zip(names, values)}
    record = {}
    record['measurement'] = measurement
    if time is not None:
        record['time'] = time
    record['fields'] = fields
    records = [record]
    return records


def composeInfluxDBDataJSON_fields(
    *,
    fields: Dict[str, Any],
    measurement: str = influxdb_default_bucket,
    tags: Optional[Dict[str, Any]] = None,
    time: Optional[str] = None,
) -> List[InfluxDBDataTypedDict]:
    # input type checks
    if isinstance(fields, dict) is False:
        raise TypeError("fields does have dictionary type.")
    if all([isinstance(key, str) for key in fields.keys()]) is False:
        raise TypeError(
            "A field key in fields dictionary does not have string type.")
    if isinstance(measurement, str) is False:
        raise TypeError("measurement of datum does not have string type.")
    if tags is not None:
        if isinstance(tags, dict) is False:
            raise TypeError("tags does have dictionary type.")
        if all([isinstance(key, str) for key in tags.keys()]) is False:
            raise TypeError(
                "A tag key in tags dictionary does not have string type.")
    if (time is not None) and (isinstance(time, str) is False):
        raise TypeError("Time does not have string type.")

    record = {}
    record['measurement'] = measurement
    if tags is not None:
        record['tags'] = tags
    if time is not None:
        record['time'] = time
    record['fields'] = fields
    records = [record]
    return records


def composeInfluxDBDataJSON_JSON(
    records: List[InfluxDBDataTypedDict]
) -> List[InfluxDBDataTypedDict]:
    # input type checks
    if isinstance(records, list) is False:
        raise TypeError(
            "JSON-formatted InfluxDB data does not have list type.")
    if all([isinstance(record, InfluxDBDataTypedDict) for record in records]) is False:
        raise TypeError(
            "Invalid type for a sample datum in JSON-formatted InfluxDB data.")

    return records
    ...

# implementation of typing.overload-decorated functions


def write_influxdb_new(
    *args,
    token: str = influxdb_default_token,
    org: str = influxdb_default_org,
    # Ensure the bucket exists in your database UI.
    bucket: str = influxdb_default_bucket,
    url: str = influxdb_default_url,
        **kwargs):
    """uploading sample data to influx DB"""
    sample_args = args
    sample_kwargs = kwargs.copy()

    # Form JSON-formatted sample data to be uploaded to influxdb server
    # depending on arguments for overloading
    N_sample_args = len(sample_args)
    N_sample_kwargs = len(sample_kwargs)

    # for test
    print(f"args = {args}")
    print(f"kwargs = {kwargs}")

    try:
        if N_sample_args == 1 or ("records" in kwargs.keys()):
            # JSON-formatted sample data
            records = composeInfluxDBDataJSON_JSON(*args, **kwargs)
        elif "fields" in kwargs.keys() and N_sample_kwargs in range(2, 5):
            records = composeInfluxDBDataJSON_fields(*args, **kwargs)
        elif N_sample_args + N_sample_kwargs == 2:
            # legacy function
            write_influxdb_legacy(*args, **kwargs)
            return
        elif N_sample_args + N_sample_kwargs in [3, 4]:
            records = composeInfluxDBDataJSON_multipleNameValues(
                *args, **kwargs)
        else:
            raise TypeError("Initial screening failed to assign the given \
                            arguments to an overloading function.")
    except TypeError as ex:
        raise TypeError(
            "Failed to specify the overloading function for the arguments.") from ex

    # for test
    print(f"sample data = {records}")

    # upload sample data above to influxdb
    # Refer to
    # https://docs.influxdata.com/influxdb/cloud/api-guide/client-libraries/python/
    # with InfluxDBClient(url=url, token=token, org=org) as client:
    #     write_api = client.write_api(write_options=SYNCHRONOUS)
    #     with client.write_api(write_options=SYNCHRONOUS) as writer:
    #         writer.write(bucket=bucket, record=records)

# # Example usage:
# update_influxdb(0.1, 'mot_fluro')


# write_influxdb_new()

# <<<<< codes for test <<<<<
if __name__ == "__main__":
    print(">>> Test codes is running...")

    print("- legacy function")
    write_influxdb_new('test', 1)
    print()

    print("- signle name-value pair")
    write_influxdb_new('test_measurement', 'test_name', 1)

    print("- multiple name-value pairs")
    # write_influxdb_new([], [])
    # write_influxdb_new(['name1', 'name2', 'name3'], [1, 2, 3])

    print("- should fail")
    # write_influxdb_new()
    # write_influxdb_new(1)
    # write_influxdb_new(['name1', 2, 'name3'], [1, 2, 3])
    print()

    print(">>> Tests finished.")
    pass


# >>>>> codes for test >>>>>
