# Setup

Requires Python 3.10+ with SQLite support and the standard library. No installation is required.

From this `candidate-pack` directory:

```sh
python3 -m unittest discover -s tests -v
```

Expected starting result: **15 tests pass**. Both bug reports concern missing coverage; the unimplemented selection function is exercised only by a test confirming its placeholder behavior. Replace that test when you implement CAL-103.

Optional isolated environment:

```sh
python3 -m venv .venv
source .venv/bin/activate
```

You can use `unittest`, so there is no need to install pytest. Run commands from `candidate-pack` so the package is on Python's import path. In VS Code, open this directory directly and select a Python 3.10+ interpreter.

To inspect a diff from the full repository:

```sh
git diff -- candidate-pack
```
