from typing import LiteralString

from anki.collection import Collection
from aqt import gui_hooks
from aqt.editor import Editor
from aqt.operations import QueryOp
from aqt.utils import show_critical, ask_user, show_info, show_warning, shortcut

from .provider import Provider, DefinitionNotFoundError, DefinitionRedirectedError, DefinitionParseError


def make_dictionary_button_clicked_handler(
        provider: Provider,
        dictionary_id: str,
        definition_config: dict[str, bool]
):
    # Function call stack:
    # handle_fetch_definition_button_clicked -> after_save -> fetch_definition -> set_definition
    #                                                                           \
    #                                                                            -> handle_fetch_definition_error (if error occurs)
    from .globals import _

    def handle_fetch_definition_button_clicked(editor: Editor):
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

            ########################### Callbacks Start ###########################
            def set_definition(html: str) -> None:
                editor.note.fields[current_field] = html
                editor.loadNoteKeepingFocus()

            def handle_fetch_definition_error(e: Exception, word: str) -> None:
                if isinstance(e, DefinitionNotFoundError):
                    show_critical(_('No definition found for "{word}"').format(word=word))
                elif isinstance(e, DefinitionRedirectedError):
                    redirected_word = e.redirected_word
                    ask_user(
                        _('"{word}" wasn\'t found. Would you like to use the definition for "{redirected_word}" instead?').format(
                            word=word, redirected_word=redirected_word),
                        callback=lambda ok: fetch_definition(redirected_word) if ok else None
                    )
                elif isinstance(e, DefinitionParseError):
                    show_critical(
                        _('Failed to parse the definition for "{word}". Please report this issue to the developer.').format(
                            word=word))
                else:
                    show_critical(_('An unexpected error occurred:\n{error}').format(error=e))

            def fetch_definition_op(col: Collection, word: str) -> str:
                definition = provider.fetch_definition(dictionary_id, word)
                if definition_config["include_audio"]:
                    definition.save_audio_files(col)
                return definition.render_html(**definition_config)

            def fetch_definition(word: str) -> None:
                op = QueryOp(
                    parent=editor.parentWindow,
                    op=lambda col: fetch_definition_op(col, word),
                    success=set_definition,
                )
                op.failure(
                    lambda e: handle_fetch_definition_error(e, word)
                ).without_collection().with_progress().run_in_background()

            ########################### Callbacks End ###########################

            if editor.note.fields[current_field]:
                ask_user(
                    _("Will overwrite existing content in the current field. Do you want to proceed?"),
                    lambda ok: fetch_definition(word) if ok else None
                )
                return

            fetch_definition(word)

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

            # Get provider
            provider_id, dictionary_id = split_ids
            provider = provider_manager.get_provider(provider_id)
            if provider is None:
                print(f"Provider not found: {provider_id}")
                continue

            # Get dictionary
            dictionary_info = provider.get_dictionary_info(dictionary_id)
            if dictionary_info is None:
                print(f"{provider.name()} doesn't support dictionary: {dictionary_id}")
                continue

            # Get definition config
            definition_config = {}
            if config is not None and "definition" in config and isinstance(config["definition"], dict):
                definition_config: dict = config["definition"]
                definition_config.setdefault("include_audio", False)
                definition_config.setdefault("include_phonemic_transcriptions", True)
                definition_config.setdefault("include_translations", True)
                definition_config.setdefault("include_examples", False)

            icon = dictionary_info.icon if dictionary_info.icon is not None else provider.icon()
            keys = "Ctrl+Shift+D"
            button = editor.addButton(
                icon=icon,
                cmd=provider_dictionary_id,
                func=make_dictionary_button_clicked_handler(provider, dictionary_id, definition_config),
                id=provider_dictionary_id,
                label="" if icon else dictionary_info.name,
                tip=f"{dictionary_info.name} ({shortcut(keys)})",
                keys=keys,
            )
            buttons.append(button)


gui_hooks.editor_did_init_buttons.append(add_editor_buttons)
