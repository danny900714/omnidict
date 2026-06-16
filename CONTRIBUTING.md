# Contributing Guidelines

🎉 Thanks for taking the time to contribute! 🎉

Before submitting your contribution, please make sure to take a moment and read through the following guidelines:

- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Reporting Issues](#reporting-issues)
    - [You have a problem](#you-have-a-problem)
    - [You have a suggestion](#you-have-a-suggestion)
- [Submitting Pull Requests](#submitting-pull-requests)
    - [Getting started](#getting-started)
    - [You have a solution](#you-have-a-solution)
- [Commit Guidelines](#commit-guidelines)
    - [Format](#format)
- [AI/LLM Contributions Policy](#aillm-contributions-policy)
- [Project Overview](#project-overview)
    - [Set Up the Development Environment](#set-up-the-development-environment)
    - [Anki Add-on Development](#anki-add-on-development)
    - [Integrate a New Dictionary Provider](#integrate-a-new-dictionary-provider)

## Reporting Issues

### You have a problem

Please be so kind as to search for any open issue already covering
your problem.

If you find one, comment on it, so we know more people are experiencing it.

If not, you can go ahead and create an issue with as much detail as you can provide.
It should include the data gathered as indicated above, along with the following:

1. How to reproduce the problem
2. What the correct behavior should be
3. What the actual behavior is

Please copy to anyone relevant (e.g. provider maintainers) by mentioning their GitHub handle
(starting with `@`) in your message.

We will do our very best to help you.

### You have a suggestion

Please be so kind as to search for any open issue already covering
your suggestion.

If you find one, comment on it, so we know more people are supporting it.

If not, you can go ahead and create an issue. Please copy to anyone relevant (e.g. provider
maintainers) by mentioning their GitHub handle (starting with `@`) in your message.

## Submitting Pull Requests

### Getting started

You should be familiar with the basics of
[contributing on GitHub](https://help.github.com/articles/using-pull-requests) and have a fork properly set up.

You MUST always create PRs with *a dedicated branch* based on the latest upstream tree.

If you create your own PR, please make sure you do it right. Also be so kind as to reference
any issue that would be solved in the PR description body,
[for instance](https://help.github.com/articles/closing-issues-via-commit-messages/)
*"Fixes #XXXX"* for issue number XXXX.

### You have a solution

Please be so kind as to search for any open issue already covering
your [problem](#you-have-a-problem), and any pending/merged/rejected PR covering your solution.

If the solution is already reported, try it out and +1 the pull request if the
solution works ok. On the other hand, if you think your solution is better, post
it with reference to the other one so we can have both solutions to compare.

If not, then go ahead and submit a PR. Please copy to anyone relevant (e.g. plugin
maintainers) by mentioning their GitHub handle (starting with `@`) in your message.

## Commit Guidelines

OmniDict uses the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)
specification. The automatic changelog tool uses these to automatically generate
a changelog based on the commit messages. Here's a guide to writing a commit message
to allow this:

### Format

```
type(scope)!: subject
```

- `type`: the type of the commit is one of the following:

    - `feat`: new features.
    - `fix`: bug fixes.
    - `docs`: documentation changes.
    - `refactor`: refactor of a particular code section without introducing
      new features or bug fixes.
    - `style`: code style improvements.
    - `perf`: performance improvements.
    - `test`: changes to the test suite.
    - `ci`: changes to the CI system.
    - `build`: changes to the build system.
    - `chore`: for other changes that don't match previous types. This doesn't appear
      in the changelog.

- `scope`: section of the codebase that the commit makes changes to. If it makes changes to
  many sections, or if no section in particular is modified, leave blank without the parentheses.
  Examples:

    - Commit that changes the `cambridge` provider:
  ```
  feat(cambridge): support English-Chenise (Traditional) Dictionary
  ```

    - Commit that changes many providers:
  ```
  style: fix inline declaration of arrays
  ```

  For changes to providers, the scope should be the provider id:

    - ✅ `fix(cambridge): commit subject`
    - ❌ `fix(provider/cambridge): commit subject`

- `!`: this goes after the `scope` (or the `type` if scope is empty), to indicate that the commit
  introduces breaking changes.

  Optionally, you can specify a message that the changelog tool will display to the user to indicate
  what's changed and what they can do to deal with it. You can use multiple lines to type this message;
  the changelog parser will keep reading until the end of the commit message or until it finds an empty
  line.

  Example (made up):

  ```
  style(agnoster)!: change dirty git repo glyph

  BREAKING CHANGE: the glyph to indicate when a git repository is dirty has
  changed from a Powerline character to a standard UTF-8 emoji. You can
  change it back by setting `ZSH_THEME_DIRTY_GLYPH`.

  Fixes #420

  Co-authored-by: Username <email>
  ```

- `subject`: a brief description of the changes. This will be displayed in the changelog. If you need
  to specify other details, you can use the commit body, but it won't be visible.

  Formatting tricks: the commit subject may contain:

    - Links to related issues or PRs by writing `#issue`. This will be highlighted by the changelog tool:
      ```
      ci: run release job when pushing tags (#3)
      ```

    - Formatted inline code by using backticks: the text between backticks will also be highlighted by
      the changelog tool:
      ```
      docs: add `CONTRIBUTING.md`
      ```

## AI/LLM Contributions Policy

AI tools can be pretty helpful for coding tasks, and we're not here to gatekeep how you get your work done.
But here's the thing—this project is maintained by volunteers who do this in their spare time.
We want to make sure we're spending our limited time effectively.

If you used AI tools meaningfully in your contribution (code generation, agentic coding assistants, etc.), please
mention it in your PR description.
Basic autocomplete doesn't count, but if an AI wrote substantial parts of your code, just let us know.

**Examples of good disclosure:**

- "Used Claude Code to generate the unit tests for this feature."
- "Used GitHub Copilot to help write the initial implementation of this function."

Here's what we're looking for:

- **You understand your code**: You should be able to explain what your contribution does and how it works.
  We want to collaborate with humans who are invested in the project.
- **Context matters**: Tell us what problem you're solving, how you tested it, and link to relevant docs.
  Small, incremental changes work better than massive generated overhauls.
- **Quality over quantity**: We'd rather have one thoughtful, well-tested contribution than ten AI-generated PRs that
  need extensive review.

As always, we reserve the right to decline any contribution.
Any submission that is in violation of this policy will be closed, and the submitter may be blocked from this repository
without warning.

## Project Overview

This project is an Anki add-on that provides a dictionary lookup feature.

### Set Up the Development Environment

1. [Fork](https://github.com/danny900714/omnidict/fork) and clone the repository.
2. Install dependencies with `uv sync`.
3. Export runtime dependencies with `uv export --no-dev --format requirements.txt -o requirements_prod.txt`.
4. Install runtime dependencies into the add-on's vendor directory with
   `uv pip install -r requirements_prod.txt -t src/omnidict/vendor`.
5. Compile gettext portable objects with `uv run scripts/compile_portable_objects.py`.
6. Create a symbolic link in Anki's add-on directory that points to the `src/omnidict` directory.

For an up-to-date example of how to set up the development environment, please refer to the [
`setup-project`](.github/actions/setup-project/action.yml) custom GitHub Action.

### Anki Add-on Development

Anki provides a basic guide on how to develop add-ons: https://addon-docs.ankiweb.net/.

### Integrate a New Dictionary Provider

To integrate a new dictionary provider (like Cambridge Dictionary, Merriam-Webster, etc.),
you need to derive a new class from `omnidict.provider.common.Provider`.
In OmniDict, providers are responsible for fetching data from the dictionary and
converting it into `omnidict.provider.common.Definition` so that OmniDict can render it as card content.

Follow the steps below to implement your own provider:

1. Create a Python file in the [`src/omnidict/provider`](./src/omnidict/provider) directory.
2. Derive a new class from `omnidict.provider.common.Provider` and implement the required class variables and methods.

   `src/omnidict/provider/my_provider.py`:
    ```python
    from .common import Provider, DictionaryInfo, Definition


    class MyProvider(Provider):
        _ID = "my-id"
        _NAME = "My Provider"
        _DICTIONARIES = {
            "english-chinese": DictionaryInfo("English–Chinese Dictionary"),
        }

        def fetch_definitions(
            self, dictionary_id: str, word: str, *, download_audio: bool
        ) -> Definition:
            # Fetch data from the dictionary and convert it into a Definition
            pass
    ```

3. Register your provider in [`src/omnidict/provider/_providers.py`](./src/omnidict/provider/_providers.py).
    ```python
    # Other imports
    from .my_provider import MyProvider

    # Append your provider class to __all__
    __all__ = [
        # Other provider classes
        MyProvider,
    ]
    ```

4. Add the test spec file at `tests/omnidict/provider/<provider-id>/spec.yaml`:

    ```yaml
    # mode specifies how the test is run:
    # online: run the test against online dictionary services
    # local-unless-ci: run the test against local test data unless running in a CI environment
    #   (generate test data by running `uv run pytest --generate-test-data <provider-id>`)
    # local: run the test against local test data. Remember to commit the generated test data so that CI can test against it.
    mode: local-unless-ci
    
    # interval specifies the interval (in seconds) between test cases when testing against online dictionary services
    interval: 3
    
    # The key inside dictionaries is the dictionary id defined in your provider class, and the value is the list of test cases for that dictionary
    dictionaries:
      english-chinese:
        # words is a list of words to test.
        # There are two syntaxes for specifying a word:
        # Short syntax: just write the word as a string.
        # Long syntax:
        #   word: the word to test
        #   error: (optional)
        #     type: the type of error expected when fetching the definition
        #     attributes: (optional) a dictionary of attributes expected to be present in the error object
        # For each test case, we recommend adding a comment explaining what the test case is testing for.
        words:
          - dictionary
          - slash   # additional information inside features that makes it two lines long ((UK also oblique (stroke)))
          - word: asdf
            error:
              type: DefinitionNotFoundError
          - word: clicked
            error:
              type: DefinitionRedirectedError
              attributes:
                redirected_word: click
    ```

5. If `mode` is set to `local-unless-ci` or `local`, generate the test data by running
   `uv run pytest --generate-test-data <provider-id>`.
   When `mode` is set to `local`, also commit the generated test data to git and add a `.gitignore` file in the
   `tests/omnidict/provider/<provider-id>` directory.

6. Run `uv run pytest` to test your provider.

For a complete example of how to implement a provider,
please refer to the [Cambridge Dictionary provider](./src/omnidict/provider/cambridge.py) implementation
and its [test spec file](./tests/omnidict/provider/cambridge-dictionary/spec.yaml).
