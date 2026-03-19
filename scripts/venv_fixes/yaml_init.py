# PyYAML 6.0.3 __init__.py (restored; wheel may omit it)
from . import loader
from .dumper import *
from .error import *
from .events import *
from .loader import *
from .nodes import *
from .tokens import *

__version__ = "6.0.3"
try:
    from .cyaml import *

    __with_libyaml__ = True
except ImportError:
    __with_libyaml__ = False

import io


def warnings(settings=None):
    if settings is None:
        return {}


def scan(stream, Loader=Loader):
    loader_inst = Loader(stream)
    try:
        while loader_inst.check_token():
            yield loader_inst.get_token()
    finally:
        loader_inst.dispose()


def parse(stream, Loader=Loader):
    loader_inst = Loader(stream)
    try:
        while loader_inst.check_event():
            yield loader_inst.get_event()
    finally:
        loader_inst.dispose()


def compose(stream, Loader=Loader):
    loader_inst = Loader(stream)
    try:
        return loader_inst.get_single_node()
    finally:
        loader_inst.dispose()


def compose_all(stream, Loader=Loader):
    loader_inst = Loader(stream)
    try:
        while loader_inst.check_node():
            yield loader_inst.get_node()
    finally:
        loader_inst.dispose()


def load(stream, Loader):
    loader_inst = Loader(stream)
    try:
        return loader_inst.get_single_data()
    finally:
        loader_inst.dispose()


def load_all(stream, Loader):
    loader_inst = Loader(stream)
    try:
        while loader_inst.check_data():
            yield loader_inst.get_data()
    finally:
        loader_inst.dispose()


def full_load(stream):
    return load(stream, FullLoader)


def full_load_all(stream):
    return load_all(stream, FullLoader)


def safe_load(stream):
    return load(stream, SafeLoader)


def safe_load_all(stream):
    return load_all(stream, SafeLoader)


def unsafe_load(stream):
    return load(stream, UnsafeLoader)


def unsafe_load_all(stream):
    return load_all(stream, UnsafeLoader)


def emit(
    events,
    stream=None,
    Dumper=Dumper,
    canonical=None,
    indent=None,
    width=None,
    allow_unicode=None,
    line_break=None,
):
    getvalue = None
    if stream is None:
        stream = io.StringIO()
        getvalue = stream.getvalue
    dumper = Dumper(
        stream,
        canonical=canonical,
        indent=indent,
        width=width,
        allow_unicode=allow_unicode,
        line_break=line_break,
    )
    try:
        for event in events:
            dumper.emit(event)
    finally:
        dumper.dispose()
    if getvalue:
        return getvalue()


def serialize_all(
    nodes,
    stream=None,
    Dumper=Dumper,
    canonical=None,
    indent=None,
    width=None,
    allow_unicode=None,
    line_break=None,
    encoding=None,
    explicit_start=None,
    explicit_end=None,
    version=None,
    tags=None,
):
    getvalue = None
    if stream is None:
        if encoding is None:
            stream = io.StringIO()
        else:
            stream = io.BytesIO()
        getvalue = stream.getvalue
    dumper = Dumper(
        stream,
        canonical=canonical,
        indent=indent,
        width=width,
        allow_unicode=allow_unicode,
        line_break=line_break,
        encoding=encoding,
        version=version,
        tags=tags,
        explicit_start=explicit_start,
        explicit_end=explicit_end,
    )
    try:
        dumper.open()
        for node in nodes:
            dumper.serialize(node)
        dumper.close()
    finally:
        dumper.dispose()
    if getvalue:
        return getvalue()


def serialize(node, stream=None, Dumper=Dumper, **kwds):
    return serialize_all([node], stream, Dumper=Dumper, **kwds)


def dump_all(
    documents,
    stream=None,
    Dumper=Dumper,
    default_style=None,
    default_flow_style=False,
    canonical=None,
    indent=None,
    width=None,
    allow_unicode=None,
    line_break=None,
    encoding=None,
    explicit_start=None,
    explicit_end=None,
    version=None,
    tags=None,
    sort_keys=True,
):
    getvalue = None
    if stream is None:
        if encoding is None:
            stream = io.StringIO()
        else:
            stream = io.BytesIO()
        getvalue = stream.getvalue
    dumper = Dumper(
        stream,
        default_style=default_style,
        default_flow_style=default_flow_style,
        canonical=canonical,
        indent=indent,
        width=width,
        allow_unicode=allow_unicode,
        line_break=line_break,
        encoding=encoding,
        version=version,
        tags=tags,
        explicit_start=explicit_start,
        explicit_end=explicit_end,
        sort_keys=sort_keys,
    )
    try:
        dumper.open()
        for data in documents:
            dumper.represent(data)
        dumper.close()
    finally:
        dumper.dispose()
    if getvalue:
        return getvalue()


def dump(data, stream=None, Dumper=Dumper, **kwds):
    return dump_all([data], stream, Dumper=Dumper, **kwds)


def safe_dump_all(documents, stream=None, **kwds):
    return dump_all(documents, stream, Dumper=SafeDumper, **kwds)


def safe_dump(data, stream=None, **kwds):
    return dump_all([data], stream, Dumper=SafeDumper, **kwds)


def add_implicit_resolver(tag, regexp, first=None, Loader=None, Dumper=Dumper):
    if Loader is None:
        loader.Loader.add_implicit_resolver(tag, regexp, first)
        loader.FullLoader.add_implicit_resolver(tag, regexp, first)
        loader.UnsafeLoader.add_implicit_resolver(tag, regexp, first)
    else:
        Loader.add_implicit_resolver(tag, regexp, first)
    Dumper.add_implicit_resolver(tag, regexp, first)


def add_path_resolver(tag, path, kind=None, Loader=None, Dumper=Dumper):
    if Loader is None:
        loader.Loader.add_path_resolver(tag, path, kind)
        loader.FullLoader.add_path_resolver(tag, path, kind)
        loader.UnsafeLoader.add_path_resolver(tag, path, kind)
    else:
        Loader.add_path_resolver(tag, path, kind)
    Dumper.add_path_resolver(tag, path, kind)


def add_constructor(tag, constructor, Loader=None):
    if Loader is None:
        loader.Loader.add_constructor(tag, constructor)
        loader.FullLoader.add_constructor(tag, constructor)
        loader.UnsafeLoader.add_constructor(tag, constructor)
    else:
        Loader.add_constructor(tag, constructor)


def add_multi_constructor(tag_prefix, multi_constructor, Loader=None):
    if Loader is None:
        loader.Loader.add_multi_constructor(tag_prefix, multi_constructor)
        loader.FullLoader.add_multi_constructor(tag_prefix, multi_constructor)
        loader.UnsafeLoader.add_multi_constructor(tag_prefix, multi_constructor)
    else:
        Loader.add_multi_constructor(tag_prefix, multi_constructor)


def add_representer(data_type, representer, Dumper=Dumper):
    Dumper.add_representer(data_type, representer)


def add_multi_representer(data_type, multi_representer, Dumper=Dumper):
    Dumper.add_multi_representer(data_type, multi_representer)


class YAMLObjectMetaclass(type):
    def __init__(cls, name, bases, kwds):
        super().__init__(name, bases, kwds)
        if "yaml_tag" in kwds and kwds["yaml_tag"] is not None:
            if isinstance(cls.yaml_loader, list):
                for ldr in cls.yaml_loader:
                    ldr.add_constructor(cls.yaml_tag, cls.from_yaml)
            else:
                cls.yaml_loader.add_constructor(cls.yaml_tag, cls.from_yaml)
            cls.yaml_dumper.add_representer(cls, cls.to_yaml)


class YAMLObject(metaclass=YAMLObjectMetaclass):
    __slots__ = ()
    yaml_loader = [Loader, FullLoader, UnsafeLoader]
    yaml_dumper = Dumper
    yaml_tag = None
    yaml_flow_style = None

    @classmethod
    def from_yaml(cls, loader_inst, node):
        return loader_inst.construct_yaml_object(node, cls)

    @classmethod
    def to_yaml(cls, dumper_inst, data):
        return dumper_inst.represent_yaml_object(
            cls.yaml_tag, data, cls, flow_style=cls.yaml_flow_style
        )
