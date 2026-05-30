# Include vendor directory into sys.path
import sys
from pathlib import Path
from typing import Any

vendor_path = str(Path(__file__).parent / "vendor")
if vendor_path not in sys.path:
    sys.path.insert(0, vendor_path)

from aqt import gui_hooks, mw
from aqt.editor import Editor, Note
from aqt.utils import show_info, show_warning, ask_user

from .cambridge import Client

# Init tasks
client = Client()


def fetch_definition(editor: Editor) -> None:
    def fetch_and_set_definition(vocabulary: str, fields: list[Any], current_field: int) -> None:
        config = mw.addonManager.getConfig(__name__)
        definition = client.fetch_definition(config["dict_code"], vocabulary)
        fields[current_field] = definition.render_html()
        editor.loadNoteKeepingFocus()

    def after_save():
        current_field = editor.currentField
        if current_field is None or editor.note is None:
            return
        if current_field == 0:
            show_info("Click the next field to fetch definition.")
            return

        vocabulary = editor.note.fields[current_field - 1]

        if not vocabulary:
            show_warning("Please enter a word in the field above to proceed.")
            return
        if editor.note.fields[current_field]:
            ask_user("Will overwrite existing content in the current field. Do you want to proceed?",
                     lambda ok: fetch_and_set_definition(vocabulary, editor.note.fields, current_field) if ok else None)
            return

        fetch_and_set_definition(vocabulary, editor.note.fields, current_field)

    editor.call_after_note_saved(after_save)


def add_fetch_definition_button(buttons: list[str], editor: Editor) -> None:
    button = editor.addButton(
        icon=None,
        cmd="cambridge_dictionary.fetch_definition",
        func=fetch_definition,
        id="fetch-definition-button",
        label="Fetch definition",
        tip="Fetch definition from Cambridge Dictionary",
        keys="Ctrl+Shift+C",
    )
    buttons.append(button)


gui_hooks.editor_did_init_buttons.append(add_fetch_definition_button)
