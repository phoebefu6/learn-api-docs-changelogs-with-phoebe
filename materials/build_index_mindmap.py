"""Write window.MINDMAP_DATA into index.html with json.dumps (never string interpolation).
Run from the repo root: python3 materials/build_index_mindmap.py"""
import json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
S = [
    ("Docs as the\nAPI's interface", "01-who-reads-the-docs.html", "#34D399",
     ["Five reader jobs", "Time to first call", "One spec feeds the kit"]),
    ("Spec-first in\nOpenAPI 3.1", "02-spec-first-openapi.html", "#34D399",
     ["Paths, operations, schemas", "Components and $ref", "Spec-first vs code-first"]),
    ("Reference pages that\nanswer the question", "03-reference-pages.html", "#FBBF24",
     ["What an endpoint page owes", "Errors with codes and fixes", "Pagination and idempotency"]),
    ("Examples\nthat run", "04-examples-that-run.html", "#FB923C",
     ["Quickstart from the spec", "A test that fails on drift", "Docs drift, measured"]),
    ("The changelog\nchecker", "05-the-changelog-checker.html", "#FB923C",
     ["28 rules, one asymmetry", "The SemVer bump", "Ship it as a minor"]),
    ("Versioning and\ndeprecation", "06-versioning-and-deprecation.html", "#F87171",
     ["URL, header or date", "Deprecation and Sunset", "Migration guide, scored"]),
]
data = {"title": "API Docs &\nChangelogs", "centerColor": "#12330E", "sessions": [
    {"label": l, "href": "courses/" + h, "color": c,
     "concepts": [{"label": x, "href": "courses/" + h} for x in cs]} for l, h, c, cs in S]}
p = ROOT / "index.html"
s = p.read_text()
block = "<script>\nwindow.MINDMAP_DATA = " + json.dumps(data, indent=1, ensure_ascii=False) + ";\n</script>"
s2 = re.sub(r"<script>\nwindow\.MINDMAP_DATA = .*?;\n</script>", lambda m: block, s, flags=re.S)
assert s2 != s or block in s
p.write_text(s2)
print("mindmap nodes:", 1 + len(S) + sum(len(x[3]) for x in S))
