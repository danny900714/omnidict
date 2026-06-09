from yaml import Dumper, SafeLoader

from omnidict.provider.common import Example, Sense, Entry, Pronunciation, Definition


class DefinitionDumper(Dumper):
    pass


def _make_representer():
    def representer(dumper, obj):
        return dumper.represent_mapping("tag:yaml.org,2002:map", obj.__dict__)

    return representer


def _definition_representer(dumper: DefinitionDumper, definition: Definition):
    return dumper.represent_mapping(
        "tag:yaml.org,2002:map",
        {
            "word": definition.word,
            "entries": definition.entries,
            "audio_files": definition.audio_files,
        },
    )


def _bytes_representer(dumper: DefinitionDumper, data: bytes):
    return dumper.represent_binary(data)


for _cls in (Example, Sense, Pronunciation, Entry):
    DefinitionDumper.add_representer(_cls, _make_representer())
DefinitionDumper.add_representer(Definition, _definition_representer)
DefinitionDumper.add_representer(bytes, _bytes_representer)


class DefinitionLoader(SafeLoader):
    pass


def _make_constructor(cls, deep=False):
    def constructor(loader, node):
        data = loader.construct_mapping(node, deep=deep)
        return cls(**data)

    return constructor


_CONSTRUCTORS = [
    ("!example", Example, False),
    ("!sense", Sense, True),
    ("!pronunciation", Pronunciation, False),
    ("!entry", Entry, True),
    ("!definition", Definition, True),
]
for _tag, _cls, _deep in _CONSTRUCTORS:
    DefinitionLoader.add_constructor(_tag, _make_constructor(_cls, _deep))

# Path resolvers for plain-map YAML documents (current dump format using tag:yaml.org,2002:map).
# These map structural positions in the document to the appropriate constructor tag.
_entry_path = [(dict, "entries"), (list, None)]
_pronunciation_path = [*_entry_path, (dict, "pronunciations"), (list, None)]
_sense_path = [*_entry_path, (dict, "senses"), (list, None)]
_example_path = [*_sense_path, (dict, "examples"), (list, None)]

DefinitionLoader.add_path_resolver("!definition", [], dict)
DefinitionLoader.add_path_resolver("!entry", _entry_path, dict)
DefinitionLoader.add_path_resolver("!pronunciation", _pronunciation_path, dict)
DefinitionLoader.add_path_resolver("!sense", _sense_path, dict)
DefinitionLoader.add_path_resolver("!example", _example_path, dict)
