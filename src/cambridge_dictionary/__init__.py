# Include vendor directory into sys.path
import sys
from pathlib import Path
from typing import Any

vendor_path = str(Path(__file__).parent / "vendor")
if vendor_path not in sys.path:
    sys.path.insert(0, vendor_path)

from aqt import gui_hooks, mw
from aqt.editor import Editor
from aqt.operations import QueryOp
from aqt.utils import show_info, show_warning, ask_user, show_critical

from .dictionary import DefinitionNotFoundError, DefinitionRedirectedError, DefinitionParseError, Definition
from .cambridge import Client

# Init tasks
client = Client()


def on_fetch_definition_button_clicked(editor: Editor) -> None:
    def set_definition(fields: list[Any], current_field: int, definition_html: str) -> None:
        fields[current_field] = definition_html
        editor.loadNoteKeepingFocus()

    def handle_fetch_definition_error(e: Any, word: str, fields: list[Any], current_field: int) -> None:
        if isinstance(e, DefinitionNotFoundError):
            show_critical(f'Failed to fetch definition for "{word}"')
        elif isinstance(e, DefinitionRedirectedError):
            redirected_word = e.redirected_word
            ask_user(
                f'Definition is redirected to "{redirected_word}". Would you like to fetch that definition?',
                callback=lambda ok: fetch_and_set_definition(redirected_word, fields, current_field) if ok else None
            )
        elif isinstance(e, DefinitionParseError):
            show_critical(
                f'Failed to parse definition for "{word}". The website structure might have changed. Please report this issue to the developer.')
        else:
            show_critical(f'An unexpected error occurred: {str(e)}')

    def fetch_and_set_definition(vocabulary: str, fields: list[Any], current_field: int) -> None:
        config = mw.addonManager.getConfig(__name__)
        op = QueryOp(
            parent=mw.app.activeWindow(),
            op=lambda _: client.fetch_definition(config["dict_code"], vocabulary).render_html(),
            success=lambda definition: set_definition(fields, current_field, definition),
        )
        op.failure(
            lambda e: handle_fetch_definition_error(e, vocabulary, fields, current_field)
        ).without_collection().with_progress().run_in_background()

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
            ask_user(
                "Will overwrite existing content in the current field. Do you want to proceed?",
                lambda ok: fetch_and_set_definition(vocabulary, editor.note.fields, current_field) if ok else None
            )
            return

        fetch_and_set_definition(vocabulary, editor.note.fields, current_field)

    editor.call_after_note_saved(after_save)


def add_fetch_definition_button(buttons: list[str], editor: Editor) -> None:
    button = editor.addButton(
        icon=None,
        cmd="cambridge_dictionary.fetch_definition",
        func=on_fetch_definition_button_clicked,
        id="fetch-definition-button",
        label="Fetch definition",
        tip="Fetch definition from Cambridge Dictionary",
        keys="Ctrl+Shift+C",
    )
    buttons.append(button)


gui_hooks.editor_did_init_buttons.append(add_fetch_definition_button)
