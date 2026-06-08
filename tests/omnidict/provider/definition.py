from yaml import Dumper, SafeLoader

from omnidict.provider.common import Example, Sense, Entry, Pronunciation, Definition


class DefinitionDumper(Dumper):
    pass


def _example_representer(dumper: DefinitionDumper, example: Example):
    return dumper.represent_mapping("tag:yaml.org,2002:map", example.__dict__)


def _sense_representer(dumper: DefinitionDumper, sense: Sense):
    return dumper.represent_mapping("tag:yaml.org,2002:map", sense.__dict__)


def _pronunciation_representer(dumper: DefinitionDumper, pronunciation: Pronunciation):
    return dumper.represent_mapping("tag:yaml.org,2002:map", pronunciation.__dict__)


def _entry_representer(dumper: DefinitionDumper, entry: Entry):
    return dumper.represent_mapping("tag:yaml.org,2002:map", entry.__dict__)


def _definition_representer(dumper: DefinitionDumper, definition: Definition):
    return dumper.represent_mapping(
        "tag:yaml.org,2002:map",
        {
            "word": definition.word,
            "entries": definition.entries,
            "audio_files": definition.audio_files,
        }
    )


def _bytes_representer(dumper: DefinitionDumper, data: bytes):
    return dumper.represent_binary(data)


DefinitionDumper.add_representer(Example, _example_representer)
DefinitionDumper.add_representer(Sense, _sense_representer)
DefinitionDumper.add_representer(Pronunciation, _pronunciation_representer)
DefinitionDumper.add_representer(Entry, _entry_representer)
DefinitionDumper.add_representer(Definition, _definition_representer)
DefinitionDumper.add_representer(bytes, _bytes_representer)


class DefinitionLoader(SafeLoader):
    pass


def _example_constructor(loader: DefinitionLoader, node) -> Example:
    data = loader.construct_mapping(node)
    return Example(**data)


def _sense_constructor(loader: DefinitionLoader, node) -> Sense:
    data = loader.construct_mapping(node, deep=True)
    return Sense(**data)


def _pronunciation_constructor(loader: DefinitionLoader, node) -> Pronunciation:
    data = loader.construct_mapping(node)
    return Pronunciation(**data)


def _entry_constructor(loader: DefinitionLoader, node) -> Entry:
    data = loader.construct_mapping(node, deep=True)
    return Entry(**data)


def _definition_constructor(loader: DefinitionLoader, node) -> Definition:
    data = loader.construct_mapping(node, deep=True)
    return Definition(**data)


# Constructors for YAML documents with explicit tags (e.g., older dumps using !definition, !entry)
DefinitionLoader.add_constructor("!example", _example_constructor)
DefinitionLoader.add_constructor("!sense", _sense_constructor)
DefinitionLoader.add_constructor("!pronunciation", _pronunciation_constructor)
DefinitionLoader.add_constructor("!entry", _entry_constructor)
DefinitionLoader.add_constructor("!definition", _definition_constructor)

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