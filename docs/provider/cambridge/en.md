# [Cambridge Dictionary] English Dictionary Parser Guide

## Web page structure

The main content is under `div.page` element.

It contains several `div.pr.dictionary` dictionary blocks which have a unique `data-id` attributes to identify them.

| `data-id` | Dictionary                                          |
|-----------|-----------------------------------------------------|
| `cald4`   | Cambridge Advanced Learner's Dictionary & Thesaurus |
| `cacd`    | Cambridge Academic Content Dictionary               |
| `cbed`    | Cambridge Business English Dictionary               |

This guide is written from `cald4`, but it transfers: `cacd` and `cbed` reuse the very same element structure, and
every selector below resolves inside them too. The few places where their element trees actually differ are called out
under the affected section; everything else holds identically for all three.

A successfully loaded page does not necessarily contain a `cald4` block. `in a nutshell`, `bide your time`,
`let something/someone slide`, `in the red`, `in the black` and `at arm's length` all return HTTP 200 while shipping a
`cacd` block only; `slack off` ships `cacd` and `cbed` but no `cald4`. A missing `cald4` block therefore has to be
handled the same way as a definition that was not found. (Those terms may still exist in `cald4` as an embedded phrase
of another headword, e.g. `in a nutshell` under `nutshell`.)

The reverse happens just as often — `fuck`, `fuck around`, `on the back of` and `back to square one` ship a `cald4`
block only. No one of the three dictionaries is a superset of the others.

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

*Other dictionaries:* the four types are not evenly distributed. `cacd` has idioms but no phrase entries, and `cbed`
had neither idiom nor phrase blocks on any sampled page — business idioms such as `cash cow`, `golden handshake`,
`loss leader` and `above board` appear there as regular word entries or as run-ons instead. `cacd` and `cbed` add a
fifth structure of their own, the run-on block for derived forms (see [Entry block](#entry-block)).

### Entry block

- Regular word: `.link > .superentry > .di-body > .entry > .entry-body > .entry-body__el`

  It contains: `.cid`, `.pos-header`, `.pos-body`

- Idiom: `.link > .superentry > .di-body > .pr.idiom-block > .idiom-block`

  It contains: `.di-title`, `span.di-info`, `span.idiom-body.didiom-body`

- Phrase: `.link > .superentry > .di-body > .pr.idiom-block > .idiom-block`

  It contains: `.di-title`, `span.di-info`, `span.phrase-di-body.dphrase-di-body`

  Note that the English dictionary has no `span.phrase-di-block.dphrase-di-block` element that the Chinese dictionary
  uses. A phrase shares the very same `.pr.idiom-block > .idiom-block` wrapper with an idiom; the two are only told
  apart by their body element (`span.idiom-body.didiom-body` vs. `span.phrase-di-body.dphrase-di-body`), which also
  matches the text of `span.di-info > span.pos.dpos` (`idiom` vs. `phrase`).

- Phrasal verb: `.link > .superentry > .di-body > .entry > .entry-body > .entry-body__el > .pr.relativDiv > .pv-block`

  It contains: `.di-title`, `span.di-info`, `span.pv-body.dpv-body`

  Note that the class name is `relativDiv`, not `relativeDiv`.

  The `.entry-body__el` wrapping a phrasal verb is an empty shell: it has neither `.pos-header` nor `.pos-body`.
  Selecting regular words by `.entry-body__el` alone therefore yields empty entries on a phrasal verb page (see
  `fuck around`), so the regular word selector has to require a direct `.pos-header`/`.pos-body` child. A single page
  can also mix both kinds (see `make something of`).

*Other dictionaries:* `cacd` and `cbed` add one container that `cald4` does not use — the run-on block, which hangs a derived form off the
parent entry's `.pos-body`:

```
.pos-body > div.pr.runon.drunon
              |-- div.cid
              |-- span.runon-head.drunon-head   (holds span.runon-title, the derived word)
              +-- div.runon-body.drunon-body > div.def-block.ddef_block.ddef_block-nos
```

e.g.: `manliness` under `man` in `cacd`, `above board` under `board` in `cbed`.

A run-on's `.def-block` is an ordinary `.def-block`, so a loose descendant selector such as `.pos-body .def-block`
swallows it as though it were a sense of the parent entry — on the `cacd` `man` page that returns 9 blocks where the
correct answer is 7. It is also the one `.def-block` whose `.ddef_h` may hold a `span.def-info` but no `.def` at all
(see `manliness` under `man`).

### Headword

The headword is the main term that appears at the beginning of each dictionary entry.

- Regular word: `.pos-header > .di-title > span.headword > span.hw`
- Idiom: `.di-title > h2.headword`
- Phrase: `.di-title > h2.headword`
- Phrasal verb: `.di-title > h2.headword`

Placeholders inside a headword are wrapped in `span.obj.dobj` (e.g. `something` in `on the back of something`).

### Part of speech

- Regular word: `.pos-header > .posgram.dpos-g > span.pos.dpos`
- Idiom: `span.di-info > span.pos.dpos`
- Phrase: `span.di-info > span.pos.dpos`
- Phrasal verb: `span.di-info > .pos-header > span.anc-info-head.danc-info-head > span.pos.dpos`

Besides the usual word classes, `.posgram` also holds `prefix` (`un-`), `suffix` (`-man`) and `collocation`
(`bode well`, `make something of someone`).

### Entry features

- Regular word: `.pos-header > span.lab > span.usage`
- Idiom: `span.di-info > span.lab > span.usage`
- Phrase: `span.di-info > span.lab > span.usage`
- Phrasal verb: `span.di-info > span.lab > span.usage`

The direct child combinator matters here: `.pos-header` also contains a `span.irreg-infls.dinfls` holding inflections
(`plural men` for `man`, `-gg-` for `bug`, `plural corpora`/`corpuses` for `corpus`,
`plural commanders-in-chief` for `commander-in-chief`), and that element carries a nested `span.lab` of its own.

A phrasal verb carries **two** unrelated `span.lab > span.usage`, and only the direct child of `span.di-info` is the
phrasal verb's own feature. The other one sits inside the nested `span.di-info > .pos-header` — the same element that
holds the base verb's pronunciation — and belongs to the base verb, so it has to be excluded:

| Phrasal verb                 | `di-info > span.lab` | nested `di-info > .pos-header > span.lab` | base verb's own entry feature |
|------------------------------|----------------------|-------------------------------------------|-------------------------------|
| `make out`                   | `informal`           | —                                         | `make` verb: —                |
| `make something/someone out` | —                    | —                                         | `make` verb: —                |
| `screw (something) up`       | `informal`           | —                                         | `screw` verb: —               |
| `bugger off`                 | `offensive`          | —                                         | `bugger` verb: —              |
| `suck up to someone`         | `informal`           | —                                         | `suck` verb: —                |
| `fuck around`                | —                    | `offensive`                               | `fuck` verb: `offensive`      |
| `goof off`                   | `informal`           | `informal`                                | `goof` verb: `informal`       |
| `creep up on someone`        | —                    | —                                         | `creep` verb: —               |

The `make out` page is what settles it: its four phrasal verbs share one base verb, yet two are `informal` and two are
unlabelled, so the direct `di-info` label cannot be a property of the base verb. Conversely the nested `.pos-header`
label appears only for `fuck around` and `goof off`, and in both cases it repeats the label the base verb carries on its
own entry — `fuck around` shows that a phrasal verb can have a labelled base verb but no feature of its own.

### Pronunciation

- Regular word: `.pos-header > span.dpron-i`

  The direct child combinator excludes the pronunciation of the inflected form held by `span.irreg-infls.dinfls`
  (see `man`, `corpus`).

  Each `span.dpron-i` contains `span.region` (`uk`/`us`), `span.pron.dpron` (phonemic transcription) and
  `.daud audio source` (audio URL).

  Entries whose part of speech is `collocation` have no `span.dpron-i` at all (see `bode well`).

- Phrasal verb: it's currently ignored since it is the pronunciation of the verb

### Guideword

Senses of a regular word are grouped by a guideword, which is unique to the English dictionary.

`.pos-body > .dsense > h3.dsense_h > span.guideword.dsense_gw`

e.g.: `flash` groups its verb senses under `(SHINE SUDDENLY)`, `(MOVE FAST)`, `(SHOW QUICKLY)`, ...

A sense group without a guideword uses `div.pr.dsense.dsense-noh` and has no `h3.dsense_h` at all. Idioms and phrasal
verbs always use the `.dsense-noh` variant, and a phrase has no `.dsense` layer at all.

> `cbed` has no guidewords at all: every one of its senses is `.dsense-noh`. `cacd` uses them like `cald4`.

### Sense block

- Regular word: `.pos-body > .dsense > .sense-body > .def-block`
- Idiom: `span.idiom-body > .dsense > .sense-body > .def-block`
- Phrase: `span.phrase-di-body > .def-block`
- Phrasal verb: `span.pv-body > .dsense > .sense-body > .def-block`

Note that a phrase has no `.dsense`/`.sense-body` layer: its `.def-block`s hang directly off `span.phrase-di-body`.

Embedded phrase is a special type of sense block that is embedded in a regular word or phrasal verb entry. Instead of
defined as `.def-block` like the sense block, it is defined as `.phrase-block` under `.sense-body` element. It contains
`.phrase-head` which contains embedded phrase's headword in `span.phrase-title`. It also has a
`.phrase-body > .def-block` which contains embedded phrase's sense body.

An entry may consist of embedded phrases only, in which case it has no `.def-block` of its own at all (see `nutshell`,
`beeline`, `mired`, `fleek`, and both phrasal verbs of `make something of`). However, search the embedded phrase 
directly seems to redirect to its dedicated page.

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

It is a direct child of `.phrase-block`, next to `.phrase-head` and `.phrase-body`. Its `href` is the path of the
dedicated page of the embedded phrase (e.g. `/dictionary/english/for-the-record` on the `record` page).

> `span.dbtn` is `cald4` only. `cacd` and `cbed` have embedded phrases, but their `.phrase-block` ends after
> `.phrase-body`, so there is no button to follow.


## Some words need to be considered

### Non-embedded entry that only contains embedded content

- on fleek
- be/become mired (down) in sth

### Non-embedded entry that only contains embedded content PLUS regular entry

- make something, anything, etc. of sth/sb
