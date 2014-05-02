from djsonapi import serial

from example.testapp import models



@serial.serializer(models.Report, mode="limited")
def serialize_report_limited(obj, **kwargs):
    """
    Serialize a report in limited mode.
    """
    # serialize_model, same as serialize_fields but with debugging information for models
    limited_data = serial.serialize_model(obj, fields=("title", "message",))
    return limited_data


@serial.serializer(models.Report, mode="full")
def serialize_report_full(obj, **kwargs):
    """
    Serialize a report in full mode.
    """
    # Get limited data
    limited_data = serialize_report_limited(obj, **kwargs)
    # Add to it
    full_data = serial.serialize_model(obj, ("status"))
    full_data.update(limited_data)
    # Return the full data
    return full_data