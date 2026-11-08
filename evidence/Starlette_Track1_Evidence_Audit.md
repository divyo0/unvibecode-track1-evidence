# UnvibeCode Track 1 — Evidence Audit of Uploaded Starlette Context

**Source of all observed counts:** uploaded `starlette-repository-context.zip` and `starlette_candidates.csv` (8 November 2026). The ZIP does not record the Git commit SHA or the local UnvibeCode/Python version. Retrieve those from your terminal for any issue submission.

## Summary
- Scanned source files: **86**; exported code sections: **877**.
- Exported source relationships: **901**.
- Suspicious CSV flags: **81**; **81 of 81** point to a destination file supported by at least one genuine import in the source file. All **901 of 901** exported file-to-file edges have that support. This check does not validate precise source lines, all symbols, or completeness.
- Symbol edge names absent from the target source AST: **0** (all named symbol edges have a same-named definition in the target source, although runtime semantics are not proven).
- **55 distinct import statements** importing from `starlette.types` have unresolved named symbols: **223 symbol occurrences** (7 unique names). **Zero `imports_symbol` edges** target `starlette/types.py`, but **55 file-level import edges** do.
- **61 of 86** source files have some chunks present in Optimal but omitted from Wider, totaling **1800 chunks**, of which **1800** are not specifically itemized as omissions. This pattern is already described in issue #318.

## Why the 81 flags are misleading
- `benchmarks/gzip_benchmark.py` imports both Python `gzip` (line 4) and `GZipMiddleware` from `starlette.middleware.gzip` (line 18). Graph links to `starlette/middleware/gzip.py` are legitimate.
- `starlette/routing.py` imports Python `types` (line 8) **and** imports ASGI-related aliases from `starlette.types` (line 26). File links to `starlette/types.py` are legitimate.
- `starlette/formparsers.py` imports `StarletteDeprecationWarning` from `starlette.exceptions` (line 13), as well as `python_multipart.exceptions` in a conditional branch (lines 22/28). The edge to `starlette/exceptions.py` is legitimate.
- `tests/middleware/test_base.py` imports from `starlette.types` (line 21) **and** `tests.types` (line 23), so both file targets are expected.

## Genuine observed missing-symbol problem
`starlette/types.py` itself defines several ASGI type aliases:

```python
Scope = MutableMapping[str, Any]             # line 12
Message = MutableMapping[str, Any]           # line 13
Receive = Callable[[], Awaitable[Message]]   # line 15
Send = Callable[[Message], Awaitable[None]]   # line 16
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]  # line 18
```

A real import in `starlette/routing.py` line 26 imports `ASGIApp`, `Lifespan`, `Receive`, `Scope`, `Send` from `starlette.types`. The downloaded ZIP's `unresolved_relationships.jsonl` reports each as `symbol_not_found`, despite the names being declared in the source. The same pattern occurs across **55 import statements / 223 symbol occurrences**. This is a missed *symbol-level* dependency, not a false file target.

**Fix direction:** The Python symbol extractor should register importable module-level type-alias bindings (`Assign`, `AnnAssign`, and `TypeAlias` where applicable), even when the assigned value is a `Callable`, `MutableMapping`, union, or generic expression. Symbol resolution should use the known module scope; preserve uncertainty if the target cannot be verified. Add a regression test with `types.py` and `consumer.py` importing those aliases.

**Novelty warning:** This mechanism substantially overlaps existing issues:
- [#295](https://github.com/FinanceFlash/unvibecode/issues/295) — module-level assignments not indexed.
- [#526](https://github.com/FinanceFlash/unvibecode/issues/526) — non-literal module-level assignments not indexed.
- [#297](https://github.com/FinanceFlash/unvibecode/issues/297) — PEP 695 type alias statements not indexed.
Thus these results alone should **not** be presented as a new original Track 1 issue.

## Other confirmed discrepancy (already reported)
Across the uploaded `selections.jsonl`, Wider drops some code sections included in Optimal for **61/86 files**. This is covered by [#318](https://github.com/FinanceFlash/unvibecode/issues/318). Do not file a duplicate.

## How to verify before submitting a new issue
1. Pin the repository: `git -C "<your-folder>\starlette" rev-parse HEAD`.
2. Record the tool version: `<your-folder>\.venv\Scripts\python.exe -m pip show unvibecode`.
3. Reproduce a **distinct** behavior on a minimal repository. Include both the source code and exact exported output/log.
4. Search all open and closed issues by the **underlying cause**, not just the repository or symptom, before claiming originality.
5. If you find a novel root cause, report Expected vs Actual, command and version, exact lines and output, impact, suspected fix, and duplicate check.

## Limitations
This audit used the ZIP artifacts, not an executable UnvibeCode build or the current checkout of Starlette. The ZIP does not contain the entire original repository, the HTML business workflow report or the Git SHA, so this report does not evaluate runtime behavior or assert a new independently reproduced defect.
