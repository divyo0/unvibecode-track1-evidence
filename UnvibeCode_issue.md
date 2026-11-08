**Title:** [Bug] Connection resolver — external imports (`_typeshed.wsgi`, `werkzeug.test`) are linked to unrelated files under `tests/`, including a `.css` file

## 1. Problem summary
On Flask, `connections.jsonl` (documented as "verified cross-file connections") links Python files in `src/flask/` to files in `tests/` that they never import. One target is a CSS file. These false links are copied into the context chunks that UnvibeCode prepares for an AI assistant, so the assistant is shown unrelated test code as if it were a dependency of the production module.

## 2. Test environment
- UnvibeCode version: [FILL IN: output of `py -m pip show unvibecode`] (`analysis-status.json` reports `runner_version: shipreadyv2.customer_mvp.v10`)
- Operating system / Python version: Windows [FILL IN: Windows version] / Python [FILL IN: python --version]
- Public repository URL and commit or release: https://github.com/pallets/flask, commit `49943b5a94413a530761350f04e896f76e8d620e` (main, 3.2.0.dev)
- Relevant command: `py -m unvibecode review --repository "<path to the cloned flask folder>"` [FILL IN: change only if you used something different]

## 3. Steps to reproduce
1. Clone Flask and check out `49943b5a94413a530761350f04e896f76e8d620e`.
2. Run UnvibeCode on the cloned folder (command above) and wait until the analysis status is COMPLETE.
3. Open `flask-repository-context.zip` and read `connections.jsonl`, or run:
   ```python
   import zipfile, json
   z = zipfile.ZipFile("flask-repository-context.zip")
   for line in z.open("connections.jsonl"):
       r = json.loads(line)
       if r["source_file"].startswith("src/") and r["target_file"].startswith("tests/"):
           print(r["source_file"], "->", r["target_file"], r["relationship"], r["confidence"])
   ```
4. Compare each printed line with the real import in the source file.

## 4. Expected behavior
`import werkzeug.test` and `from _typeshed.wsgi import ...` are imports of external packages. They should be left unresolved (they already appear in `unresolved_relationships.jsonl` for other files), not linked to repository files. A Python import should never resolve to a `.css` file. Production code under `src/` should not be reported as depending on `tests/`.

## 5. Actual behavior
The script prints 10 records (9 distinct file pairs) from `src/` to `tests/`. Seven of them come from external imports:

| Source file | Real import in source | Linked to | Relationship |
|---|---|---|---|
| `src/flask/testing.py` | line 11: `import werkzeug.test` | `tests/test_apps/blueprintapp/apps/admin/static/css/test.css` | `imports_module` + `file_import`, medium |
| `src/flask/app.py` | line 56: `from _typeshed.wsgi import StartResponse` | `tests/test_apps/helloworld/wsgi.py` | `file_import`, medium |
| `src/flask/cli.py` | line 30: `from _typeshed.wsgi import StartResponse` | same `wsgi.py` | `file_import`, medium |
| `src/flask/ctx.py` | line 19: `from _typeshed.wsgi import WSGIEnvironment` | same `wsgi.py` | `file_import`, medium |
| `src/flask/testing.py` | line 21: `from _typeshed.wsgi import WSGIEnvironment` | same `wsgi.py` | `file_import`, medium |
| `src/flask/typing.py` | line 7: `from _typeshed.wsgi import WSGIApplication` | same `wsgi.py` | `file_import`, medium |

`test.css` contains only `/* nested file */`. `wsgi.py` contains `from hello import app`.

## 6. Evidence
- Source lines: the import lines in the table above (all are in the Flask repo at the stated commit; the `_typeshed` imports are under `TYPE_CHECKING`).
- Output excerpt (`connections.jsonl`, sanitized):
  `src/flask/testing.py -> tests/test_apps/blueprintapp/apps/admin/static/css/test.css  imports_module  medium`
- The links reach the LLM context: in `selections.jsonl`, `src/flask/testing.py` scope `1` includes the `test.css` chunk, and scope `2` also includes `wsgi.py`. `src/flask/app.py` scope `2` includes `wsgi.py`.
- Name pattern: the external module's last name segment equals the stem of the wrongly chosen file (`wsgi` and `test`), and the file extension is ignored.

## 7. Impact and scope
Wrong answer, not a crash. The connected-code map and the AI context contain false dependencies, and `medium` confidence edges are still counted in the manifest as "verified_cross_file_connections". Tested on two repositories: Flask shows the problem; Starlette (same checks on its context ZIP) showed 0 links from production code to `tests/` and 0 links to non-`.py` files. So it appears to depend on file names in the repository, which makes it harder to notice.

## 8. Suspected cause / suggested fix (if known)
Not confirmed, because I did not read the resolver source. My hypothesis: for imports that cannot be resolved inside the package, the resolver falls back to matching the module's last name segment against file stems anywhere in the repo. To check: log which strategy produced these edges. A possible fix is to skip the fallback for absolute imports whose top-level package is not in the repository (`_typeshed`, `werkzeug`), and to only accept `.py` targets for Python imports.
The same name pattern may also explain the `import typing` / `import logging` links to `src/flask/typing.py` and `src/flask/logging.py`; I have not counted those here. A different case I saw, `from .globals import app_ctx` linked to a pytest fixture in `tests/conftest.py` (3 records), looks like a separate cause (a symbol defined by assignment rather than `def`), so I am not including it here.

## 9. Duplicate check
[FILL IN: links to the issues you searched, open and closed, with the search terms. Example terms: "tests", "connections", "resolver", "css", "wsgi", "false positive".] None of them describes external imports being linked to files under `tests/`. [Only write this sentence if it is true after you search.]
