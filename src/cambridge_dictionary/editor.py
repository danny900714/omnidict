from typing import Any, LiteralString

from aqt import mw, gui_hooks
from aqt.editor import Editor
from aqt.operations import QueryOp
from aqt.utils import show_critical, ask_user, show_info, show_warning

from .provider import Provider, DefinitionNotFoundError, DefinitionRedirectedError, DefinitionParseError


def make_fetch_definition_button_clicked_handler(editor: Editor, provider: Provider, dictionary_id: str):
    from .globals import _

    def set_definition(fields: list[Any], current_field: int, html: str) -> None:
        fields[current_field] = html
        editor.loadNoteKeepingFocus()

    def handle_fetch_definition_error(e: Exception, word: str, fields: list[Any], current_field: int) -> None:
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

    def fetch_and_set_definition(word: str, fields: list[Any], current_field: int) -> None:
        op = QueryOp(
            parent=mw.app.activeWindow(),
            op=lambda _: provider.fetch_definition(dictionary_id, word).render_html(),
            success=lambda html: set_definition(fields, current_field, html),
        )
        op.failure(
            lambda e: handle_fetch_definition_error(e, word, fields, current_field)
        ).without_collection().with_progress().run_in_background()

    def after_save():
        current_field = editor.currentField
        if current_field is None or editor.note is None:
            return
        if current_field == 0:
            show_info(_("Click the next field to fetch definition."))
            return

        word = editor.note.fields[current_field - 1]

        if not word:
            show_warning(_("Please enter a word in the field above to proceed."))
            return
        if editor.note.fields[current_field]:
            ask_user(
                _("Will overwrite existing content in the current field. Do you want to proceed?"),
                lambda ok: fetch_and_set_definition(word, editor.note.fields, current_field) if ok else None
            )
            return

        fetch_and_set_definition(word, editor.note.fields, current_field)

    def handle_fetch_definition_button_clicked(_: Editor):
        editor.call_after_note_saved(after_save)

    return handle_fetch_definition_button_clicked


def add_editor_buttons(buttons: list[str], editor: Editor) -> None:
    from .globals import config, provider_manager

    if "editor" in config and "buttons" in config["editor"] and isinstance(config["editor"]["buttons"], list):
        for provider_dictionary_id in config["editor"]["buttons"]:
            split_ids: list[LiteralString] = provider_dictionary_id.split(".")
            if len(split_ids) != 2:
                print(f"Invalid provider dictionary id in config.editor.buttons: {provider_dictionary_id}")
                continue

            provider_id, dictionary_id = split_ids
            provider = provider_manager.get_provider(provider_id)
            if provider is None:
                print(f"Provider not found: {provider_id}")
                continue

            dictionary_info = provider.get_dictionary_info(dictionary_id)
            if dictionary_info is None:
                print(f"{provider.name()} doesn't support dictionary: {dictionary_id}")
                continue

            button = editor.addButton(
                icon=None,
                cmd=provider_dictionary_id,
                func=make_fetch_definition_button_clicked_handler(editor, provider, dictionary_id),
                id=provider_dictionary_id,
                label=dictionary_info.name,
                tip=f"Fetch definition from {dictionary_info.name} ({provider.name()})",
                keys="Ctrl+Shift+C",
            )
            buttons.append(button)


gui_hooks.editor_did_init_buttons.append(add_editor_buttons)
