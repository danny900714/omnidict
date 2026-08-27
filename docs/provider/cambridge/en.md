# [Cambridge Dictionary] English Dictionary Parser Guide

## Web page structure

The main content is under `div.page` element.

It contains several `div.pr.dictionary` dictionary blocks which have a unique `data-id` attributes to identify them.

| `data-id` | Dictionary                                          |
|-----------|-----------------------------------------------------|
| `cald4`   | Cambridge Advanced Learner's Dictionary & Thesaurus |
| `cacd`    | Cambridge Academic Content Dictionary               |
| `cbed`    | Cambridge Business English Dictionary               |

- `cald4` only: `fuck`, `fuck around`, `on the back of`, `back to square one`
- `cacd` only: `in a nutshell`, `bide your time`, `let something/someone slide`, `in the red`, `in the black` and `at arm's length`
- `cacd` and `cbed`: `slack off`

Inside a dictionary block every entry lives under `div.link > div.pr.di.superentry > div.di-body`, whose only meaningful
direct children are `div.entry` and `div.pr.idiom-block`.

### Types of entries

1. Regular word

   e.g.: flash

2. Idiom

   e.g.: on the back of something

3. Phrase

   e.g.: back to back

4. Phrasal verb

   e.g.: fuck around

5. Run-on (only in `cacd` and `cbed`)

   e.g.: manliness (under man in `cacd`)

### Entry block

- Regular word: `.link > .superentry > .di-body > .entry > .entry-body > .entry-body__el`

  It contains: `.cid`, `.pos-header`, `.pos-body`

- Idiom: `.link > .superentry > .di-body > .pr.idiom-block > .idiom-block`

  It contains: `.di-title`, `span.di-info`, `span.idiom-body.didiom-body`

- Phrase: `.link > .superentry > .di-body > .pr.idiom-block > .idiom-block`

  It contains: `.di-title`, `span.di-info`, `span.phrase-di-body.dphrase-di-body`

- Phrasal verb: `.link > .superentry > .di-body > .entry > .entry-body > .entry-body__el > .pr.relativDiv > .pv-block`

  It contains: `.di-title`, `span.di-info`, `span.pv-body.dpv-body`

- Run-on (only in `cacd` and `cbed`): hangs a derived form off the parent entry's `.pos-body`:

  ```
  .pos-body > div.pr.runon.drunon
                |-- div.cid
                |-- span.runon-head.drunon-head   (holds span.runon-title, the derived word)
                +-- div.runon-body.drunon-body > div.def-block.ddef_block.ddef_block-nos
  ```
  
  e.g.: `manliness` under `man` in `cacd`.

### Headword

The headword is the main term that appears at the beginning of each dictionary entry.

- Regular word: `.pos-header > .di-title > span.headword > span.hw`
- Idiom: `.di-title > h2.headword`
- Phrase: `.di-title > h2.headword`
- Phrasal verb: `.di-title > h2.headword`
- Run-on: `span.runon-head > h3.runon-title > span.w.dw`

### Part of speech

- Regular word: `.pos-header > .posgram.dpos-g > span.pos.dpos`
- Idiom: `span.di-info > span.pos.dpos`
- Phrase: `span.di-info > span.pos.dpos`
- Phrasal verb: `span.di-info > .pos-header > span.anc-info-head.danc-info-head > span.pos.dpos`
- Run-on: `span.runon-head > .pos-header > span.pos.dpos`

### Entry features

- Regular word: `.pos-header > span.lab > span.usage`
- Idiom: `span.di-info > span.lab > span.usage`
- Phrase: `span.di-info > span.lab > span.usage`
- Phrasal verb: `span.di-info > span.lab > span.usage` (see `make out`, `screw (something) up`, and `goof off`)

`.pos-header` also contains a `span.irreg-infls.dinfls` holding inflections
(`plural men` for `man`, `-gg-` for `bug`, `plural corpora`/`corpuses` for `corpus`,
`plural commanders-in-chief` for `commander-in-chief`), and that element carries a nested `span.lab` of its own.

### Pronunciation

- Regular word: `.pos-header > span.dpron-i`

  Each `span.dpron-i` contains `span.region` (`uk`/`us`), `span.pron.dpron` (phonemic transcription) and
  `.daud audio source` (audio URL).

- Phrasal verb: it's currently ignored since it is the pronunciation of the verb

### Sense block

- Regular word: `.pos-body > .dsense > .sense-body > .def-block`
- Idiom: `span.idiom-body > .dsense > .sense-body > .def-block`
- Phrase: `span.phrase-di-body > .def-block`
- Phrasal verb: `span.pv-body > .dsense > .sense-body > .def-block`

Embedded phrase is a special type of sense block that is embedded in a regular word or phrasal verb entry. Instead of
defined as `.def-block` like the sense block, it is defined as `.phrase-block` under `.sense-body` element. It contains
`.phrase-head` which contains embedded phrase's headword in `span.phrase-title`. It also has a
`.phrase-body > .def-block` which contains embedded phrase's sense body.

### Sense features

`.ddef_h > span.def-info` (exclude `span.epp-xref` and `.ddivide`)

`span.epp-xref.dxref` is the CEFR level capsule (`A1`–`C2`). `.ddivide` is a separator that introduces extra whitespace
(see `corpus`, whose third sense reads `medical  specialized`).

`span.def-info` may also hold `span.gram.dgram` (`[ I or T ]`), `span.lab.dlab`, `span.domain.ddomain` and a
`div.lmt-10` + `span.var.dvar` pair which renders the variant on a second line (see `slash`, whose noun sense carries
`(UK also oblique, oblique stroke)`).

`span.lab.dlab > span.usage.dusage` may appear under `.ddef_h > .def` (see `man`). That information needs to be extracted
and should not be included in the sense definition.

### Sense definition

`.ddef_h > .def`

The definition itself may start with a `span.lab > span.usage`, e.g. the `abbreviation` of `abbreviation for central
processing unit` in `CPU`.

### Sense example block

`.def-body > .examp`

`.def-body` holds more than examples: the cross reference blocks (`div.xref.synonym`, `div.xref.see_also`, ...) and the
usage note (`div.usagenote.dusagenote.daccord`) are siblings of `.examp` there.

### Example sentence

`span.eg`

An `.examp` is not only the sentence: it may be preceded by `span.lu.dlu`/`a.lu.dlu` (the collocation the example
illustrates, e.g. `flash something in something`), `span.gram.dgram` or `span.lab.dlab`.

### Embedded phrase "See more" button

`span.dbtn > a.hbtn.hbtn-tab.bh.tc-w.tb`

## Some words need to be considered

### Non-embedded entry that only contains embedded content

- on fleek
- be/become mired (down) in sth

### Non-embedded entry that only contains embedded content PLUS regular entry

- make something, anything, etc. of sth/sb
