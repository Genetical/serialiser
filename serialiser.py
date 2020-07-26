import sys
import importlib
from typing import Any

SERIALISED_SIGNATURE = ("__module__", "__name__", "values")


def serialise(obj: Any, no_head: bool = False) -> dict:
    """Takes any non-primitive object and serialises it into a dict.
    Arguments:
        obj(Any): Any non primitive object.
        no_head(bool): Will not specify the module and class of the object when True.
    Returns:
        dict: A serialised dictionary of all the values of an object. May also contain the module and class.
    Raises:
         TypeError: Raised when a built in object is given.

    """
    if obj.__class__.__module__ == '__builtin__':
        raise TypeError("Can't serialise a builtin type.")

    cls = obj.__class__
    if no_head:
        dct = {"values": {}}
    else:
        dct = {"__module__": cls.__module__,
               "__name__": cls.__name__,
               "values": {}}
    for i in dir(obj):
        try:
            val = getattr(obj, i)
        except AttributeError:
            val = None
        if i.startswith("_") or callable(val) or i in vars(cls):
            continue
        elif not isinstance(val, (str, int, bool, dict)) and val is not None:
            try:
                val = serialise(val)
                print(val)
            except RecursionError:
                val = str(val)
        dct["values"][i] = val
    if no_head:
        return dct["values"]
    else:
        return dct


def deserialise(dct: dict, cls: Any = None) -> Any:
    """Takes a dict and deserialises it back into its object.
    Arguments:
        dct(dict): The data to be deserialised.
        cls(Any): The object class. Must be specified if the dict is headless.
    Returns:
        Any: The original object that was serialised.
    Raises:
        ValueError: No class was specified for a headless dict.
        ModuleNotFoundError: Could not find the class specified in the dict header.
        RecursionError: A subclass deserialisation is causing a, most likely, infinite recursion.
        AttributeError: A nested, serialised object did not have a header.
        TypeError: The given class is not the same as the one stored in the dict header.
    """
    headless = tuple(dct.keys()) != SERIALISED_SIGNATURE
    if cls is None:
        if headless:
            raise ValueError(f"Must specify class for headless dict. (Expected {SERIALISED_SIGNATURE})")
        try:
            module = dct["__module__"]
            module = sys.modules[module]
        except KeyError:
            try:
                module = importlib.import_module(dct["__module__"])
            except KeyError:
                raise ModuleNotFoundError(f"Could not find module '{dct['module']}' containing {dct['__name__']}"
                                          "Pass the class to be instantiated instead.")
        try:
            cls = getattr(module, dct["__name__"])
        except AttributeError:
            raise ModuleNotFoundError(f"Could not find {dct['__name__']} in {cls.__name__}. "
                                      "Most likely an invalid module.")

    if headless or cls.__name__ == dct["__name__"]:
        for attr, val in dct["values"].items():
            if isinstance(val, dict):
                if tuple(val.keys()) == SERIALISED_SIGNATURE:
                    try:
                        dct["values"][attr] = deserialise(val)
                    except RecursionError:
                        raise RecursionError(f"Recursion caused most likely by looping subclass ({val})")
                elif tuple(val.keys()) == ("values",):
                    raise AttributeError(f"Cannot deserialise a headless subclass ({val})")
        obj = cls.__new__(cls, **dct["values"])
        for attr, val in dct["values"].items():
            setattr(obj, attr, val)
        return obj
    else:
        raise TypeError("Given class name does not match dict name."
                        f"'{cls.__name__}' given. ('{dct['name']}' expected.")
