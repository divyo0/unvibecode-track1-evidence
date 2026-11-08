"""Repro for Flask 3.2.0.dev Flask.__init_subclass__ ctx-signature shim bugs.
Run: python repro_ctx_shim.py   (needs Flask main branch / 3.2.0.dev)
"""
import warnings
from flask import Flask


def depth(f):
    n = 0
    while hasattr(f, "__wrapped__"):
        f = f.__wrapped__
        n += 1
    return n


print("== Bug 1: aliased override crashes at class creation")
def my_handler(self, ctx, e):
    return "handled"
try:
    class Aliased(Flask):
        handle_exception = my_handler
    print("OK")
except AttributeError as e:
    print("FAIL:", e)

print("== Bug 1b: decorator without functools.wraps")
def deco(f):
    def wrapper(self, ctx, *a, **k):
        return f(self, ctx, *a, **k)
    return wrapper
try:
    class Decorated(Flask):
        @deco
        def log_exception(self, ctx, exc_info): ...
    print("OK")
except AttributeError as e:
    print("FAIL:", e)

print("== Bug 3: new-style override, param not named ctx")
with warnings.catch_warnings(record=True):
    warnings.simplefilter("always")
    class NewStyle(Flask):
        def handle_exception(self, context, e):
            return "ok"
app = NewStyle(__name__)
app.config["PROPAGATE_EXCEPTIONS"] = False
@app.route("/")
def boom():
    raise RuntimeError
try:
    print("status", app.test_client().get("/").status_code)
except TypeError as e:
    print("FAIL:", e)

print("== Bug 2: wrappers stack on shared Flask class")
before = depth(Flask.update_template_context)
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    for i in range(50):
        ns = {}
        exec("def update_template_context(self, context): ...", ns)
        type(f"Legacy{i}", (Flask,), {"update_template_context": ns["update_template_context"]})
print("depth before:", before, "after 50 legacy subclasses:", depth(Flask.update_template_context))
