# [Cambridge Dictionary] Chinese Dictionary Parser Guide

## Web page structure

The main content is under `div.di-body` element.

### Types of entries

1. Regular word

   e.g.: flash

2. Idiom

   e.g.: on the back of something

3. Phrase

   e.g.: back-to-back

### Entry block

- Regular word: `div.entry > div.entry_body > div.pr.entry-body__el`

  It contains: `.cid`, `.pos-header`, `.pos-body`

- Idiom: `div.pr.idiom-block > div.idiom-block`

  It contains: `.di-title`, `.di-info`, `.idiom-body.didiom-body`

- Phrase: `span.phrase-di-block.dphrase-di-block`

  It contains: `.di-title`, `.di-info`, `.phrase-di-body.dphrase-di-body`

- Phrasal verb: `div.entry > div.entry_body > div.pr.entry-body__el > div.pr.relativeDiv > div.pv-block`

  It contains: `.di-title`, `span.di-info`, `span.pv-body.dpv-body`

### Headword

The headword is the main term that appears at the beginning of each dictionary entry.

- Regular word: `.pos-header >  .di-title > span.headword > span.hw`
- Idiom: `.di-title > h2.headword`
- Phrase: `.di-title > h2.headword`
- Phrasal verb: `.di-title > h2.headword`

### Part of speech

- Regular word: `.pos-header > .posgram.dpos-g.hdib > (span.pos.dpos)`
- Idiom: `span.di-info > span.pos.dpos`
- Phrase: `span.di-info > span.pos.dpos`
- Phrasal verb: `span.di-info > .pos-header > span.anc-info-head.danc-info-head > span.pos.dpos`

### Entry features

- Regular word: `.pos-header > span.lab > span.usage`
- Idiom: `span.di-info > span.lab > span.usage`

### Pronunciation

- Regular word: `.pos-header > span.dpron-i`
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

### Sense definition

`.ddef_h > .def`

### Sense translation

`.def-body > span.trans`

### Sense example block

`.def-body > .examp`

### Example sentence

`span.eg`

### Example translation

`span.trans`

### Embedded phrase "See more" button

`span.dbtn > a.hbtn.hbtn-tab.bh.tc-wtb`

## When should consider a match?

There are lots of cases that a search term input from users is different from the entry's headword, but that entry
should be included in the word definition.

We listed some common patterns we found in headwords and the search word below:

- **Hyphen**

  Hyphens before (suffix), after (prefix) or in the middle of the headword should consider a match.

  Examples:
    - -man
    - un-
    - back-to-back


- **Slash**

  Slashes can be used to separate multiple meanings or forms of a headword.

  Examples:
    - be at the mercy of someone/something
    - have/take a gander


- **Parentheses**

  Parentheses make some words optional in a phrase.

  Examples:
    - be/get/run low (on something)
    - be/become mired (down) in sth


- **Comma**

  Like slashes, commas can be used to separate multiple forms of specific word in a phrase.

  Examples:
    - make something, anything, etc. of sth/sb


- **Placeholder**

  Placeholder can present between the words in a headword or after the headword, especially when the placeholder is a
  phrase. Slash can be used to separate multiple placeholders.

  Examples:
    - on the back of **something**

## Some words need to be considered

### Hyphens

- [commander-in-chief](https://dictionary.cambridge.org/dictionary/english-chinese-traditional/commander-in-chief)
- [in-residence](https://dictionary.cambridge.org/dictionary/english-chinese-traditional/in-residence)

### Embedded phrases

- [in a nutshell](https://dictionary.cambridge.org/dictionary/english-chinese-traditional/nutshell?q=in+a+nutshell)
- [make a beeline for someone/something](https://dictionary.cambridge.org/dictionary/english-chinese-traditional/beeline?q=make+a+beeline+for+someone%2Fsomething)

### Have a non-embedded entry but redirect to the embedded one

- back to back
- be crawling with something
- be at the mercy of someone/something
- get on someone's nerves
- be incumbent on/upon someone
- have/take a gander
- be confined to somewhere/something
- compose your features/thoughts
- be/get/run low (on something)

### Non-embedded entry that only contains embedded content

- make something, anything, etc. of sth/sb **(it's also a phrasal verb)**
- on fleek
- be/become mired (down) in sth
- bide your time
- catch someone red-handed

### Only the English dictionary has entries

- have skin in the game
- slack off
- no harm no foul
- grind someone's gears
- be not above
- bode well
- take a dive
- flip the script
- get/have your ducks in a row
- go to hell in a handcart
- up a/the creek without a paddle
- the icing on the cake
- up the creek without a puddle
- have a good head on your shoulders
- run your mouth
- in the weeds
- broad stroke
- bar none
- push the envelope
- let something/someone slide
