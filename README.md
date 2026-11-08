# UnvibeCode Track 1: evidence and extra work

Author: Divy Mathur, Bennett University (B.Tech CSE, 3rd year)

I ran UnvibeCode on two public repositories, Flask (commit `49943b5a94413a530761350f04e896f76e8d620e`) and Starlette, and checked the output against the real source code.

## Track 1 issue

The issue write-up, in the format the challenge asks for, is in [`UnvibeCode_issue.md`](UnvibeCode_issue.md).

**Finding:** on Flask, `connections.jsonl` links production files in `src/flask/` to files under `tests/` that they never import, because external imports (`_typeshed.wsgi`, `werkzeug.test`) are matched to same-named repo files. One of those targets is a `.css` file. These links are also copied into the context chunks prepared for an AI assistant.

## Reproduce

```
pip install unvibecode
py -m unvibecode review --repository "<path to a clone of flask at the commit above>"
python check_connections.py
```

`check_connections.py` finds every `*-repository-context.zip` under the current folder and prints:

| Repository | Production file to `tests/` | Python file to non-`.py` file |
|---|---|---|
| Flask | 10 records | 2 records |
| Starlette | 0 | 0 |

The full output is in [`evidence/check_output.txt`](evidence/check_output.txt).

## What is in `evidence/`

| File | What it is |
|---|---|
| `check_output.txt` | Output of `check_connections.py` for both repositories |
| `flask_suspicions.csv` | Leads taken from the connection data (a script flagged them, I verified them by hand) |
| `starlette_candidates.csv`, `starlette_confirmed_missing_symbol_imports.csv`, `Starlette_Track1_Evidence_Audit.md` | Starlette checks. All 81 flagged links were backed by real imports, so I did not report them. The missing-symbol pattern matches mechanisms that were already reported, so I did not file it again. |
| `unvibecode_reports/` | The UnvibeCode result pages for Flask (zero reportable risks) |

Leads I checked and rejected: Flask `import typing` / `import logging` links to `src/flask/typing.py` and `src/flask/logging.py` (not counted in the issue), and `from .globals import app_ctx` linked to a pytest fixture (different cause, overlaps an existing report).

## Extra work (not part of the Track 1 issue)

[`extra/flask-ctx-shim/`](extra/flask-ctx-shim) holds a reproduction and a candidate patch for a separate bug I found in Flask 3.2.0.dev, in `Flask.__init_subclass__`: aliased or undecorated method overrides raise `AttributeError` when the class is defined. Run `python repro_ctx_shim.py` in an environment where Flask was installed from the cloned repository (`pip install -e <flask folder>`). It does not reproduce on the released Flask 3.1.x.
