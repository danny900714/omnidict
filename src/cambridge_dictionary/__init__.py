from aqt import gui_hooks
from aqt.editor import Editor

from .cambridge import Client


def fetch_definition(editor: Editor) -> None:
    print("fetch_definition")
    client = Client()
    pass


def add_fetch_definition_button(buttons: list[str], editor: Editor) -> None:
    button = editor.addButton(
        icon=None,
        cmd="cambridge_dictionary.fetch_definition",
        func=fetch_definition,
        label="Fetch definition",
        tip="Fetch definition from Cambridge Dictionary",
        keys="Ctrl+Shift+C",
    )
    buttons.append(button)
    pass


gui_hooks.editor_did_init_buttons.append(add_fetch_definition_button)
