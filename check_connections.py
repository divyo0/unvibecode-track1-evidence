"""List suspicious edges in UnvibeCode repository-context ZIP files.

Run it from your UnvibeCodeChallenge folder with no arguments and it finds every
*-repository-context.zip below the current folder:

    python check_connections.py

Or name one ZIP (or a folder to search):

    python check_connections.py path\\to\\flask-repository-context.zip

An edge is flagged when a production file (not under tests/, docs/ or examples/)
is linked to a file under tests/, or when a .py file is linked to a non-.py file.
Compare each flagged edge with the real import line in the source file.
"""
import json
import sys
import zipfile
from pathlib import Path


def find_zips(args):
    targets = [Path(a) for a in args] or [Path.cwd()]
    found = []
    for t in targets:
        if t.is_file() and t.suffix == ".zip":
            found.append(t)
        elif t.is_dir():
            found.extend(sorted(t.rglob("*repository-context.zip")))
    # drop duplicates, keep order
    seen, unique = set(), []
    for p in found:
        key = p.resolve()
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return unique


def is_prod(path):
    return not path.startswith(("tests/", "docs/", "examples/"))


def shown(path):
    try:
        return str(Path(path).resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return Path(path).name


def check(zip_path):
    with zipfile.ZipFile(zip_path) as z:
        if "connections.jsonl" not in z.namelist():
            print(f"{shown(zip_path)}: no connections.jsonl inside, skipped")
            return
        rows = [json.loads(line) for line in z.open("connections.jsonl")]

    to_tests = [r for r in rows
                if is_prod(r["source_file"]) and r["target_file"].startswith("tests/")]
    non_py = [r for r in rows
              if r["source_file"].endswith(".py") and not r["target_file"].endswith(".py")]

    print(f"\n=== {shown(zip_path)}")
    print(f"{len(rows)} connections in total")
    print(f"\nproduction file -> tests/ file: {len(to_tests)}")
    for r in to_tests:
        print(f'  {r["source_file"]} -> {r["target_file"]}'
              f'  [{r["relationship"]}, symbol={r["symbol"]}, {r["confidence"]}]')
    print(f"\nPython file -> non-.py file: {len(non_py)}")
    for r in non_py:
        print(f'  {r["source_file"]} -> {r["target_file"]}'
              f'  [{r["relationship"]}, {r["confidence"]}]')


def main():
    zips = find_zips(sys.argv[1:])
    if not zips:
        print("No *-repository-context.zip found.")
        print("Run this from the UnvibeCodeChallenge folder, or pass the ZIP path:")
        print("    python check_connections.py path\\to\\flask-repository-context.zip")
        sys.exit(1)
    for z in zips:
        check(z)


if __name__ == "__main__":
    main()
