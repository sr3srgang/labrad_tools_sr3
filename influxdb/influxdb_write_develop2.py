# 2024/11/03 Modified by Joonseok Hur

 dateutil.parser
from typing import TypedDict
from typing import Iterable, Dict, Any, Union, Optional, overload
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

# default influxdb info
influxdb_default_token = "yelabtoken"
influxdb_default_org = "yelab"
# Ensure the bucket exists in your database UI.
influxdb_default_bucket = "sr3"
influxdb_default_url = "http://yemonitor.colorado.edu:8086"


# >>>>> legacy function for uploading data to Ye Sr Group's influxDB >>>>>


def write_influxdb_legacy(name, value):
    """
    Update InfluxDB with a single value and a name.

    :param value: The value to write to the database.
    :param name: The name associated with the value.
    """
    # legacy influxdb upload parameters
    influxdb_default_token = "yelabtoken"
    influxdb_default_org = "yelab"

    # Ensure the bucket exists in your database UI.
    influxdb_default_bucket = "sr3"
    influxdb_default_url = "http://yemonitor.colorado.edu:8086"

    with InfluxDBClient(url=influxdb_default_url, token=influxdb_default_token, org=influxdb_default_org) as client:
        write_api = client.write_api(write_options=SYNCHRONOUS)

        # Format the data for the database server
        message = f"live_data,host=myhost {name}={value}"

        write_api.write(influxdb_default_bucket, influxdb_default_org, message)

        # print(message)  # Print to the console
# <<<<< legacy function for uploading data to Ye Sr Group's influxDB <<<<<<


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
# #            timestamp in UTC is assinged if the timestamp is not
# #            included with the point.
# # measurement: a high-level description of all timestamped data
# #              collected. it only takes str and does not have
# #              key-value pairing unlike tags and fields below. It can
# #              be compared to the title of a table.
# # fields: key-value pairs that store actual data value. A key takes
# #         the type of the data (e.g., "voltage[V]", "frequency[Hz]",
# #         "temperature[degC]") and the associated value takes the
# #         value of the data. A key can be compared to a main column
# #         in a table, to write measurement results, labeled as the
# #         key in the head cell.
# #         The associated values to the key from different timestamped
# #         sample data corresponds to the values in the cells below
# #         the head cell along the column below from the rows for
# #         data measured at different times, respectively.
# #         The field key should have string type and field value can
# #         take four data types: bool, int, float, and stirng.
# #         The fields are not indexed or provide fast query, which
# #         should make sense considering the intended use of the
# #         fields. (e.g., it would not be usual to query the sample
# #         data with a particular temperature, say, 10.65 degC.)
# # tags: Optional. key-value pair that records metadata of the actual
# #       data. Each value takes further description, of the same type
# #       described in the key paired with the value, of each
# #       timestamped sample data. (e.g., "JH", "YY", "MT", "MM" values
# #       for "researcher name" key; "breadboard surface", "laser diode
# #       mount", "ambient at room center" values for "measurement
# #       location" key; "1st", "2nd", "3rd" values for "priority" key.)
# #       A key and associated values can be compared as the header
# #       label and contents in a column for additional descrition of
# #       each measurement.
# #       The tag key and value should have string type.
# #       The tags are indexed and therefore provide fast & efficient
# #       queries on a tag value, which is natural useful. (e.g., when
# #       query the data measured by a "researcher name" "JH" ;or the
# #       temperature at the "location" "laser diode mount".)
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

# TODO: update type declearation for time from str to str or int


# # types of (overloading) influxdb functions arguments
# Measurement = str
# TagKey = str
# TagValue = str
# Tags = Dict[TagKey, TagValue]
# Time = Union[int, str]
# FieldKey = str
# FieldValue = Union[bool, int, float, str],
# Fields = Dict[FieldKey, FieldValue]

# define arguments for overloading functions

@overload
def write_influxdb_new(
    measurement: str, name: str, value: Union[bool, int, float, str],
    time: Optional[Union[int, str]] = None,
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
    measurement: str, names: Iterable[str], values: Iterable[Union[bool, int, float, str]],
    time: Optional[Union[int, str]] = None,
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
    tags: Optional[Dict[str, str]] = None,
    time: Optional[Union[int, str]] = None,
    fields: Dict[str, Union[bool, int, float, str]],
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
    tags: Optional[Dict[str, str]]
    time: Optional[Union[int, str]]
    fields: Dict[str, Union[bool, int, float, str]]


@overload
def write_influxdb_new(
    record: InfluxDBDataTypedDict, *,
    token: str = influxdb_default_token,
    org: str = influxdb_default_org,
    # Ensure the bucket exists in your database UI.
    bucket: str = influxdb_default_bucket,
    url: str = influxdb_default_url
) -> None:
    """ Uploading JSON-formatted sample datum to InfluxDB"""
    ...


@overload
def write_influxdb_new(
    records: Iterable[InfluxDBDataTypedDict], *,
    token: str = influxdb_default_token,
    org: str = influxdb_default_org,
    # Ensure the bucket exists in your database UI.
    bucket: str = influxdb_default_bucket,
    url: str = influxdb_default_url
) -> None:
    """ Uploading JSON-formatted sample data to InfluxDB"""
    ...


@overload
def write_influxdb_new(
    name: str, value: Union[bool, int, float, str]
) -> None:
    """ (DEPRECATED) Legacy function for uploading one (name, value) pair to
    InfluxDB before 2024/11/06. Use other overloading functions"""
    ...


# functions to check sample data-related input arguments
# https://docs.influxdata.com/influxdb/v1/write_protocols/line_protocol_reference/#data-types

def verifyInput_measurement(measurement):
    if isinstance(measurement, str) is False:
        raise TypeError("measurement does not have string type.")


def verifyInput_tagKey(tag_key):
    if isinstance(tag_key, str) is False:
        raise TypeError("Tag key does not have string type.")


def verifyInput_tagValue(tag_value):
    if isinstance(tag_value, str) is False:
        raise TypeError("Tag value does not have string type.")


def verifyInput_tags(tags):
    if isinstance(tags, dict) is False:
        raise TypeError("tags does not have dictionary type.")
    for tag_key in tags.keys():
        verifyInput_tagKey(tag_key)
        verifyInput_tagValue(tags[tag_key])


# from datetime import datetime
# def isisotime(str: str) -> bool:
#     """return if a given string is in ISO 8601 time format or not

#     Args:
#         str (str): string argument to be checked

#     Returns:
#         bool: true if string argument has the form of iso time
#     """
#     try:
#         datetime.fromisoformat(str)
#     except:
#         return False
#     return True


def verifyInput_time(time):
    # TODO: check for int for Unix nanosecond timestamp (e.g., +1730862677120000000) or
    # a string for ISO 8601 expression for date and time in UTC
    # (e.g, "2024-11-06T03:11:17.12Z"; "T" is the delimiter between date and time
    # and "Z" for zero UTC offset (i.e., UTC time))
    # https://en.wikipedia.org/wiki/Unix_time
    # https://en.wikipedia.org/wiki/ISO_8601

    # TODO: minimum timestamp (-9223372036854775806 or "1677-09-21T00:12:43.145224194Z")
    # & max timestamp (9223372036854775806 or "2262-04-11T23:47:16.854775806Z")
    unix_time_ns = time
    if isinstance(time, (int, str)) is False:
        raise TypeError("Time does not have int or string type.")
    elif isinstance(time, str) is True:
        # if isisotime(time) is False:
        #     raise TypeError("Time string does not have ISO 8601 format.")
        try:
            # unix nanosecond time
            # unix_time_ns = datetime.fromisoformat(time).timestamp()
            unix_time_ns = dateutil.parser.isoparse(time).timestamp()*1e9
        except:
            raise TypeError("Time string does not have ISO 8601 format.")

    if unix_time_ns < -9223372036854775806:
        raise ValueError("Time is behind the minimum valid time: "
                         "-9223372036854775806 or "
                         "\"1677-09-21T00:12:43.145224194Z\"")
    if unix_time_ns > +9223372036854775806:
        raise ValueError("Time is ahead of the maximum valid time: "
                         "+9223372036854775806 or "
                         "\"2262-04-11T23:47:16.854775806Z\"")


def verifyInput_fieldKey(field_key):
    if isinstance(field_key, str) is False:
        raise TypeError("Field of datum does not have string type.")


def verifyInput_fieldValue(field_value):
    if isinstance(field_value, (bool, int, float, str)) is False:
        raise TypeError(
            "Field of datum does not have bool, int, float, or string type.")


def verifyInput_fields(fields):
    if isinstance(fields, dict) is False:
        raise TypeError("fields does have dictionary type.")

    for field_key in fields.keys():
        verifyInput_fieldKey(field_key)
        verifyInput_fieldValue(fields[field_key])


def verifyInput_JSONDatum(record):
    if isinstance(record, dict) is False:
        raise TypeError("JSON datum does have dictionary type.")

    # check all the keys are valid
    keys_datum_required = {"measurement", "fields"}
    keys_datum_optional = {"time", "tags"}
    keys_record = set(record.keys())
    keys_record_required = keys_record.copy()
    for key_datum_optional in keys_datum_optional:
        if key_datum_optional in keys_record:
            keys_record_required.remove(key_datum_optional)
    # # for test
    # print(
    #     f"keys_datum: required={keys_datum_required}, optional={keys_datum_optional}")
    # print(f"keys_record: input={keys_record}, required={keys_record_required}")
    if keys_datum_required != keys_record_required:
        raise TypeError("Invalid key set in JSON datum.")

    # check value type of each key
    verifyInput_measurement(record["measurement"])
    verifyInput_fields(record["fields"])
    if "time" in keys_record:
        verifyInput_time(record["time"])
    if "tags" in keys_record:
        verifyInput_tags(record["tags"])


def verifyInput_JSONData(records):
    if isinstance(records, Iterable) is False:
        raise TypeError("JSON data does have Iterable type.")

    [verifyInput_JSONDatum(record) for record in records]


# functions to compose JSON for influxDB

def composeInfluxDBJSONData_singleNameValue(
    measurement: str, name: str, value: Union[bool, int, float, str],
    time: Optional[Union[int, str]] = None,
) -> Iterable[InfluxDBDataTypedDict]:
    # input type checks
    verifyInput_measurement(measurement)
    verifyInput_fieldKey(name)
    verifyInput_fieldValue(value)
    if time is not None:
        verifyInput_time(time)

    fields = {name: value}
    record = {}
    record['measurement'] = measurement
    if time is not None:
        record['time'] = time
    record['fields'] = fields
    records = [record]
    return records


def composeInfluxDBJSONData_multipleNameValues(
    measurement: str, names: Iterable[str], values: Iterable[Any],
    time: Optional[Union[int, str]] = None
) -> Iterable[InfluxDBDataTypedDict]:
    # input type checks
    verifyInput_measurement(measurement)
    if len(names) != len(values):
        raise TypeError("name and value Iterables have different lengths.")
    [verifyInput_fieldKey(name) for name in names]
    [verifyInput_fieldValue(value) for value in values]
    # if all([isinstance(name, str) for name in names]) is False:
    #     raise TypeError(
    #         "A name in name Iterable does not have string type.")
    if time is not None:
        verifyInput_time(time)

    fields = {name: value for name, value in zip(names, values)}
    record = {}
    record['measurement'] = measurement
    if time is not None:
        record['time'] = time
    record['fields'] = fields
    records = [record]
    return records


def composeInfluxDBJSONData_fields(
    *,
    fields: Dict[str, Union[bool, int, float, str]],
    measurement: str = influxdb_default_bucket,
    tags: Optional[Dict[str, Any]] = None,
    time: Optional[Union[int, str]] = None,
) -> Iterable[InfluxDBDataTypedDict]:
    # input type checks
    verifyInput_fields(fields)
    verifyInput_measurement(measurement)
    if tags is not None:
        verifyInput_tags(tags)
    if time is not None:
        verifyInput_time(time)


does not have ISO 8601 format.")

    if unix_time_ns < -9223372036854775806:
        raise ValueError("Time is behind the minimum valid time: "
                         "-9223372036854775806 or "
                         "\"1677-09-21T00:12:43.145224194Z\"")
    if unix_time_ns > +9223372036854775806:
        raise ValueError("Time is ahead of the maximum valid
    if tags is not None:
        record['tags'] = tags
    if time is not None:
        record['time'] = time
    record['fields'] = fields
    records = [record]
    return records


def composeInfluxDBJSONData_datum(
    record: InfluxDBDataTypedDict
) -> Iterable[InfluxDBDataTypedDict]:
    # input type checks
    verifyInput_JSONDatum(record)

    records = [record]
    return records


def composeInfluxDBJSONData_data(
    records: Iterable[InfluxDBDataTypedDict]
) -> Iterable[InfluxDBDataTypedDict]:
    # input type checks
    verifyInput_JSONData(records)

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

    # check influxDB-related input arguments' types'
    if isinstance(token, str) is False:
        raise TypeError("Token for influxDB does not have string type.")
    if isinstance(org, str) is False:
        raise TypeError("Org for influxDB does not have string type.")
    if isinstance(bucket, str) is False:
        raise TypeError("Bucket in influxDB does not have string type.")
    if isinstance(url, str) is False:
        raise TypeError("URL of influxDB does not have string type.")

    keys_kwargs = set(kwargs.keys())

    N_args = len(args)
    N_kwargs = len(kwargs)

    # for test
    print(f"args = {args}, kwargs = {kwargs}, "
          f"N__ars = {N_args}, N_kwargs = {N_kwargs}")

    try:
        if N_args + N_kwargs == 1:
            if N_args > 0:
                records = args[0]
                if isinstance(records, dict) is True:
                    # JSON-formatted sample datum
                    records = composeInfluxDBJSONData_datum(
                        *args, **kwargs)
                else:
                    # JSON-formatted sample data
                    records = composeInfluxDBJSONData_data(
                        *args, **kwargs)
            elif "record" in keys_kwargs:
                # JSON-formatted sample datum
                records = composeInfluxDBJSONData_datum(
                    *args, **kwargs)
            elif "records" in keys_kwargs:
                # JSON-formatted sample data
                records = composeInfluxDBJSONData_data(
                    *args, **kwargs)
            else:
                raise TypeError("Failed to determine the overloading function for "
                                "single vs multiple JSON-formatted data.")

        elif "fields" in kwargs.keys() and N_kwargs in range(2, 5):
            records = composeInfluxDBJSONData_fields(
                *args, **kwargs)
        elif N_args + N_kwargs == 2:
            # legacy function
            # write_influxdb_legacy(*sample_args, **sample_kwargs)

            # for test
            print(f"Legacy function called.\n")
            return
        elif N_args + N_kwargs in [3, 4]:
            if len(args) >= 2:
                names = args[1]
                if isinstance(names, str) is True:
                    records = composeInfluxDBJSONData_singleNameValue(
                        *args, **kwargs)
                else:
                    records = composeInfluxDBJSONData_multipleNameValues(
                        *args, **kwargs)
            elif "name" in keys_kwargs:
                records = composeInfluxDBJSONData_singleNameValue(
                    *args, **kwargs)
            elif "names" in keys_kwargs:
                records = composeInfluxDBJSONData_multipleNameValues(
                    *args, **kwargs)
            else:
                raise TypeError("Failed to determine the overloading function"
                                "for single vs multiple name-value pair(s).")

        else:
            raise TypeError("Initial screening failed to assign the given"
                            "arguments to an overloading function.")
    except TypeError as ex:
        raise TypeError(
            "Failed to specify the overloading function for the arguments.") from ex

    # for test
    # print(f"sample data = {records}")
    # print()

    # # upload sample data above to influxdb
    # # Refer to
    # # https://docs.influxdata.com/influxdb/cloud/api-guide/client-libraries/python/
    # with InfluxDBClient(url=url, token=token, org=org) as client:
    #     write_api = client.write_api(write_options=SYNCHRONOUS)
    #     with client.write_api(write_options=SYNCHRONOUS) as writer:
    #         writer.write(bucket=bucket, record=records)


# <<<<< codes for test <<<<<
if __name__ == "__main__":
    print(">>> Test codes is running...\n")

    name = 'test_name'
    value = 1

    # print("- legacy function")
    # write_influxdb_new('test_name', 1)
    # write_influxdb_new('test_name', value=1)
    # write_influxdb_new(name='test_name', value=1)
    # print()

    measurement = "test_measurement"
    time_ISO8601 = "2024-11-06T03:11:17.12Z"
    time_UnixTime_ns = +1730862677120000000

    # print("- signle name-value pair")
    # write_influxdb_new(measurement, name, value)
    # write_influxdb_new(measurement, name, value=value)
    # write_influxdb_new(measurement, name=name, value=value)
    # write_influxdb_new(measurement=measurement, name=name, value=value)
    # write_influxdb_new(measurement, name, value, time_ISO8601)
    # write_influxdb_new(measurement, name, value, time_UnixTime_ns)
    # write_influxdb_new(measurement, name, value, time=time_ISO8601)
    # write_influxdb_new(measurement, name, value=value, time=time_ISO8601)
    # write_influxdb_new(measurement, name=name, value=value, time=time_ISO8601)
    # write_influxdb_new(measurement=measurement, name=name,
    #                    value=value, time=time_ISO8601)
    # print()

    # write_influxdb_new(measurement, name, value,
    #                    "1677-09-21T00:12:43.145224194Z")

    names = ['test_name1', 'test_name2', 'test_name3', 'test_name4']
    values = [True, 2, 3.51, "test_value4"]

    # print("- multiple name-value pairs")
    # write_influxdb_new(measurement, names, values)
    # write_influxdb_new(measurement, names, values=values)
    # write_influxdb_new(measurement, names=names, values=values)
    # write_influxdb_new(measurement=measurement, names=names, values=values)
    # write_influxdb_new(measurement, names, values, time_ISO8601)
    # write_influxdb_new(measurement, names, values, time_UnixTime_ns)
    # write_influxdb_new(measurement, names, values, time=time_ISO8601)
    # write_influxdb_new(measurement, names, values=values, time=time_ISO8601)
    # write_influxdb_new(measurement, names=names,
    #                    values=values, time=time_ISO8601)
    # write_influxdb_new(measurement=measurement, names=names,
    #                    values=values, time=time_ISO8601)
    print()

    tag = 1
    tags = {"test_tag_key1": "test_tag_value1",
            "test_tag_key2": "test_tag_value2", }
    fields = {"test_field_key1": True, "test_field_key2": 1,
              "test_field_key3": 0.65, "test_field_key4": "test_field_value4", }

    # print("- one sample datum")
    # write_influxdb_new(measurement=measurement, fields=fields)
    # write_influxdb_new(measurement=measurement, tags=tags, fields=fields)
    # write_influxdb_new(measurement=measurement,
    #                    time=time_ISO8601, fields=fields)
    # write_influxdb_new(measurement=measurement, tags=tags,
    #                    time=time_ISO8601, fields=fields)
    # print()

    # print("- JSON-formatted sample datum")
    # write_influxdb_new(
    #     {
    #         "measurement": measurement,
    #         "fields": fields,
    #     }
    # )
    # write_influxdb_new(
    #     {
    #         "measurement": measurement,
    #         "tags": tags,
    #         "fields": fields,
    #     }
    # )does not have ISO 8601 format.")

    if unix_time_ns < -9223372036854775806:
        raise ValueError("Time is behind the minimum valid time: "
                         "-9223372036854775806 or "
                         "\"1677-09-21T00:12:43.145224194Z\"")
    if unix_time_ns > +9223372036854775806:
        raise ValueError("Time is ahead of the maximum valid
    #     }
    # )
    # write_influxdb_new(
    #     {
    #         "measurement": measurement,
    #         "tags": tags,
    #         "time": time_ISO8601,
    #         "fields": fields,
    #     }
    # )
    # print()

    # print("- JSON-formatted sample data")
    # write_influxdb_new(
    #     [
    #         {
    #             "measurement": measurement,
    #             "fields": fields,
    #         },
    #         {
    #             "measurement": measurement,
    #             "tags": tags,
    #             "fields": fields,
    #         },
    #         {
    #             "measurement": measurement,
    #             "time": time_ISO8601,
    #             "fields": fields,
    #         },
    #         {
    #             "measurement": measurement,
    #             "tags": tags,
    #             "time": time_ISO8601,
    #             "fields": fields,
    #         },
    #     ]
    # )
    # print()

    bucket = "sr3"

    # print("- InfluxDB setting")
    # write_influxdb_new(measurement, name, value, bucket=bucket)
    # print()

    print("- should fail")
    # # no or not enough arguments
    # write_influxdb_new()
    # write_influxdb_new(1)
    # # undefined arguments
    # write_influxdb_new(measurement, name, value, undefinedArgument=1)

    # # invalid input type for single name or value
    # write_influxdb_new(1, name, value)
    # write_influxdb_new(measurement, 1, value)
    # write_influxdb_new(measurement, 1, {})
    # write_influxdb_new(measurement, name, [])
    # write_influxdb_new(measurement, name, values)
    # write_influxdb_new(measurement, [], value)
    # write_influxdb_new(measurement, names, value)
    # write_influxdb_new(measurement, names, value, "afsd")
    # write_influxdb_new(measurement, names, value, 1.5)
    # write_influxdb_new(measurement, names, value, [])

    # # invalid input value for time
    write_influxdb_new(measurement, name, value, -9223372036853775807)
    # write_influxdb_new(measurement, name, value,
    #                    "1677-09-21T00:12:43.145224195Z")
    # write_influxdb_new(measurement, name, value,
    #                    "1677-09-21T00:12:43.145224094Z")
    # write_influxdb_new(measurement, name, value, -9223372036854775809)
    # write_influxdb_new(measurement, name, value, +9223372036854775807)
    write_influxdb_new(measurement, name, value,
                       "2262-04-11T23:47:16.854775807Z")
    # write_influxdb_new(measurement, name, value,
    #                    "2262-04-11T23:47:16.854776807Z")

    # # invalid input type in multiple names or values
    # write_influxdb_new(measurement, ['name1', 2, 'name3'], values)
    # write_influxdb_new(measurement, names, [1, [], 3])

    # # invalid input

    # print()

    print(">>> Tests finished.")
    pass


# >>>>> codes for test >>>>>
