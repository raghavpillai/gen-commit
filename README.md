# Gen Commit

Gen Commit automatically generate git commit messages. I'm lazy and don't like to write commit messages. Inspired by [scommit](https://github.com/Globe-Engineer/semantic-commit).

![Wow!](assets/logs.png)

---

## Usage

gencommit works exactly like git commit, but it generates the commit message for you.

```bash
gencommit
```

is the same as

```bash
git commit -m "..." -m "..."
```

but with a generated commit message.

You can also pass in the same arguments as git commit.

```bash
gencommit -a
```

is the same as

```bash
git commit -a -m "..." -m "..."
```

## Installation

### Prerequisites:

- Python 3.11+

Install the gen-commit package using pip:

```bash
pip install gen-commit
```

Once you have it installed, initialize gencommit

```bash
gencommit --init
```

Go to `~/.gen-commit` and add your OpenAI or Anthropic API key.

### Configuration

```bash
MODEL=<provider:model (i.e. openai:gpt-4o or anthropic:claude-3-haiku-20240307)>
OPENAI_API_KEY=<your openai api key>
ANTHROPIC_API_KEY=<your anthropic api key>
```

At the moment only OpenAI and Anthropic are supported.
