import sys
import importlib


def serialise(obj) -> dict:
    if obj.__class__.__module__ == '__builtin__':
        raise TypeError("Can't serialise a builtin type.")
    cls = obj.__class__
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
    return dct


def deserialise(dct: dict, cls=None):
    if cls is None:
        try:
            module = dct["__module__"]
            module = sys.modules[module]
        except KeyError:
            try:
                module = importlib.import_module(dct["__module__"])
            except KeyError:
                raise ModuleNotFoundError(f"Could not find module containing {dct['__name__']}"
                                          "Pass the class to be instantiated instead.")
        cls = getattr(module, dct["__name__"])

    if cls.__name__ == dct["__name__"]:
        for attr, val in dct["values"].items():
            if isinstance(val, dict) and tuple(val.keys()) == ("__name__", "__module__", "values"):
                dct["values"][attr] = deserialise(val)
        obj = cls.__new__(cls, **dct["values"])
        for attr, val in dct["values"].items():
            setattr(obj, attr, val)
        return obj
    else:
        raise TypeError("Given class name does not match dict name."
                        f"'{cls.__name__}' given. ('{dct['name']}' expected.")
