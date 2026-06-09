## `definition`

Controls what information is fetched and rendered when a definition is added to a card.

**`include_audio`** — boolean, default: `false`  
Download pronunciation audio files and embed them in the card.

**`include_phonemic_transcriptions`** — boolean, default: `true`  
Show phonemic (IPA) transcriptions alongside each pronunciation.

**`include_translations`** — boolean, default: `true`  
Show the translation for each sense and its example sentences.

**`include_examples`** — boolean, default: `false`  
Show example sentences for each sense.

## `editor`

Controls which dictionary buttons appear in the Anki card editor toolbar.

### `buttons`

A list of dictionary identifiers. Each entry adds one button to the editor toolbar. The format is:

`{provider-id}.{dictionary-id}`

**Supported values**

- `cambridge-dictionary.english-chinese-traditional`: Cambridge English–Chinese (Traditional) Dictionary
- `cambridge-dictionary.english-chinese-simplified`: Cambridge English–Chinese (Simplified) Dictionary
