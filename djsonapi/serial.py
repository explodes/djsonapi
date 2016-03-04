import itertools
import json

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder


## JSON Methods

def dump(obj, fp, **kwargs):
    """
    Write the JSON serialization of `obj` to `fp`.

    Uses Django"s encoder in order to automatically encode date, datetime, and Decimal objects.

    `args` and `kwargs` are the same as a regular json.dumps call, except that `kwargs["cls"]` is modified.
    """
    kwargs["cls"] = DjangoJSONEncoder
    return json.dump(obj, fp, **kwargs)


def dumps(obj, **kwargs):
    """
    Convert python objects to JSON.

    Uses Django"s encoder in order to automatically encode date, datetime, and Decimal objects.

    `args` and `kwargs` are the same as a regular json.dumps call, except that `kwargs["cls"]` is modified.
    """
    kwargs["cls"] = DjangoJSONEncoder
    return json.dumps(obj, **kwargs)

# Shortcut for json.load
load = json.load
# Shortcut for json.loads
loads = json.loads


## Serializer Methods

# (klass, mode) => serializer_func registration map
SERIAL_MAP = {}
# Whether or not to, by default, include object debug information.
SERIALIZE_DEBUG_DATA = settings.DEBUG


class NoSerializerFound(Exception):
    """
    Raised when no serializer is found for a (klass, mode) combination.
    """


def _get_serialize_func(klass, mode):
    """
    Return the registered serializer function for the given (class, mode) combo

    Raises NoSerializerFound if no serializer was found for the combination
    """
    try:
        serializer_func = SERIAL_MAP[(klass, mode)]
    except KeyError:
        raise NoSerializerFound("No serializer found for class %r and mode %r" % (klass.__name__, mode))
    else:
        return serializer_func


def _serialize_item(model_instance, mode, **kwargs):
    """
    Serialize an individual item.

    Optional `kwargs` for the serializer function are passed down.
    """
    serializer_func = _get_serialize_func(model_instance.__class__, mode)
    return serializer_func(model_instance, **kwargs)


def serializer(klass, mode=None):
    """
    Decorator to register a function as a serializer for a given (class, mode) combo.

    The function should accept optional keyword arguments, but is not required.

    i.e.

    ```
    @serializer(User)
    def serialize_any_user(obj, **kwargs):
        return {
            "name" : obj.name,
        }

    @serializer(User, mode="current_user")
    def serialize_current_user(obj, **kwargs):
        return {
            "name" : obj.name,
            "secret" : obj.secret
        }
    ```

    Which can be used by:

    data = serial.serialize(user, mode="current_user")
    data = serial.serialize(user)

    """

    def decorator(func):
        # Register the serializer function for the combination of klass and mode
        SERIAL_MAP[(klass, mode)] = func
        # Return the function unmodified
        return func

    return decorator


def serialize(items, mode=None, **kwargs):
    """
    Perform object serialization with a given mode.

    If a sequence of items is passed in, each item is serialized
    individually with the given mode and a list of data is returned.

    Optional `kwargs` for the serializer function are passed down.
    """
    if hasattr(items, "__len__"):
        # For each item, serialize that mofo.
        return [_serialize_item(item, mode, **kwargs) for item in items]
    else:
        # Serialize that mofo.
        return _serialize_item(items, mode, **kwargs)


def iserialize(items, mode=None, **kwargs):
    """
    Perform object serialization on a list of objects, returning a generator, should the need arise.

    Optional `kwargs` for the serializer function are passed down.
    """
    mappable = lambda item: _serialize_item(item, mode, **kwargs)
    return itertools.imap(mappable, items)


def serialize_fields(obj, fields):
    """
    Put the value of each attribute name in `fields` into a dict and return the dict.

    If a field is callable, it will be called with no arguments.

    e.g.

    class example:
        a = 1
        b = 2

        def c(self):
            return 3

    bag = serialize_fields(example(), ("a", "b", "c"))

    bag == {"a": 1, "b": 2, "c": 3}

    """
    bag = {}
    for name in fields:
        field = getattr(obj, name)
        bag[name] = field() if callable(field) else field
    return bag


def serialize_model(obj, fields=None, debug_fields=SERIALIZE_DEBUG_DATA):
    """
    Serialize a django model.

    Automatically serializes all fields (that don"t contain "password") if none are specified.

    `debug_fields` is `True` by default in `DEBUG` mode. This adds two fields: `pk` and `model`.
    """
    if not fields:
        fields = [field for field in obj._meta.get_all_field_names() if "password" not in field]

    bag = serialize_fields(obj, fields)

    if debug_fields:
        bag["_debug_pk"] = obj.pk
        bag["_debug_model"] = ".".join((obj._meta.app_label, obj._meta.object_name))

    return bag





