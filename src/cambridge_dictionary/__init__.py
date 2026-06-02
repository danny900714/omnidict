# Include vendor directory into sys.path
import sys
from pathlib import Path
from typing import Any, LiteralString, Optional

vendor_path = str(Path(__file__).parent / "vendor")
if vendor_path not in sys.path:
    sys.path.insert(0, vendor_path)

from aqt import gui_hooks, mw
from aqt.editor import Editor
from aqt.operations import QueryOp
from aqt.utils import show_info, show_warning, ask_user, show_critical

from .translation import _
from .dictionary import DefinitionNotFoundError, DefinitionRedirectedError, DefinitionParseError, Definition
from .cambridge import Client
from .provider import ProviderManager, Dictionary

# Init tasks
client = Client()
config = mw.addonManager.getConfig(__name__)
provider_registry = ProviderManager(config)


def on_fetch_definition_button_clicked(editor: Editor) -> None:
    def set_definition(fields: list[Any], current_field: int, definition_html: str) -> None:
        fields[current_field] = definition_html
        editor.loadNoteKeepingFocus()

    def handle_fetch_definition_error(e: Any, word: str, fields: list[Any], current_field: int) -> None:
        if isinstance(e, DefinitionNotFoundError):
            show_critical(_('No definition found for "{word}"').format(word=word))
        elif isinstance(e, DefinitionRedirectedError):
            redirected_word = e.redirected_word
            ask_user(
                _('"{word}" wasn\'t found. Would you like to use the definition for "{redirected_word}" instead?').format(
                    word=word, redirected_word=redirected_word),
                callback=lambda ok: fetch_and_set_definition(redirected_word, fields, current_field) if ok else None
            )
        elif isinstance(e, DefinitionParseError):
            show_critical(
                _('Failed to parse the definition for "{word}". Please report this issue to the developer.').format(
                    word=word))
        else:
            show_critical(_('An unexpected error occurred:\n{error}').format(error=e))

    def fetch_and_set_definition(vocabulary: str, fields: list[Any], current_field: int) -> None:
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
            show_info(_("Click the next field to fetch definition."))
            return

        vocabulary = editor.note.fields[current_field - 1]

        if not vocabulary:
            show_warning(_("Please enter a word in the field above to proceed."))
            return
        if editor.note.fields[current_field]:
            ask_user(
                _("Will overwrite existing content in the current field. Do you want to proceed?"),
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


def add_editor_buttons(buttons: list[str], editor: Editor) -> None:
    if "editor" in config and "buttons" in config["editor"] and isinstance(config["editor"]["buttons"], list):
        for provider_dictionary_id in config["editor"]["buttons"]:
            split_ids: list[LiteralString] = provider_dictionary_id.split(".")
            if len(split_ids) != 2:
                print(f"Invalid provider dictionary id in config.editor.buttons: {provider_dictionary_id}")
                continue

            provider_id, dict_id = split_ids
            provider = provider_registry.get_provider(provider_id)
            if provider is None:
                print(f"Provider not found: {provider_id}")
                continue

            dict_instance: Optional[Dictionary] = None
            for d in provider.dictionaries:
                if d.id() == dict_id:
                    dict_instance = d
                    break
            if dict_instance is None:
                print(f"Dictionary ({dict_id}) not found for provider ({provider_id})")
                continue

            dict_name = dict_instance.name()
            button = editor.addButton(
                icon=None,
                cmd=provider_dictionary_id,
                func=on_fetch_definition_button_clicked,
                id=provider_dictionary_id,
                label=dict_name,
                tip=f"Fetch definition from {dict_name} ({provider.name()})",
                keys="Ctrl+Shift+C",
            )
            buttons.append(button)


# gui_hooks.editor_did_init_buttons.append(add_fetch_definition_button)
gui_hooks.editor_did_init_buttons.append(add_editor_buttons)
