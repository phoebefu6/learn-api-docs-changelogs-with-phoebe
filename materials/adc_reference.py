"""Python reference for the changelog checker (assets/adc-live.js), by Phoebe Fu.

Same rule table, same traversal, same output as the browser engine. Used to
1. unit-test every rule against a PASSING pair (the rule fires) and a FAILING pair (a near miss
   where it must not fire):            python3 materials/adc_reference.py test
2. print the canon ladder for every preset in assets/adc-sample.js:
                                       python3 materials/adc_reference.py ladder > /tmp/py.json
   materials/compare-ladder.py compares that against node (materials/adc-node.js) by value.

Rule basis (read at source 2026-11-16): oasdiff breaking-changes list (oasdiff.com/docs/breaking-changes
and /checks/<id>) and GitHub REST "API versions" breaking vs additive lists
(docs.github.com/en/rest/about-the-rest-api/api-versions). Where they disagree the choice is noted.
"""
import copy
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
METHODS = ["get", "put", "post", "delete", "options", "head", "patch", "trace"]

RULES = {
    "OP_REMOVED": ("breaking", "Removed", "op"),            # oasdiff api-path-removed-without-deprecation (with deprecation: info; SemVer still says major)
    "OP_ADDED": ("non-breaking", "Added", "op"),            # oasdiff endpoint-added (info); GitHub additive
    "OP_DEPRECATED": ("non-breaking", "Deprecated", "op"),  # SemVer rule 7: deprecation is a minor
    "SECURITY_CHANGED": ("breaking", "Changed", "op"),      # GitHub: changing auth is breaking (oasdiff: security added = info)
    "PARAM_REMOVED": ("breaking", "Removed", "field"),      # GitHub breaking; oasdiff request-parameter-removed = warning
    "PARAM_ADDED_REQUIRED": ("breaking", "Changed", "op"),  # oasdiff new-required-request-parameter
    "PARAM_ADDED_OPTIONAL": ("non-breaking", "Added", "field"),
    "PARAM_BECAME_REQUIRED": ("breaking", "Changed", "op"),  # oasdiff request-parameter-became-required
    "PARAM_BECAME_OPTIONAL": ("non-breaking", "Changed", "field"),
    "PARAM_DEPRECATED": ("non-breaking", "Deprecated", "field"),
    "REQ_BODY_BECAME_REQUIRED": ("breaking", "Changed", "op"),
    "REQ_PROP_REMOVED": ("breaking", "Removed", "field"),    # GitHub: removing a parameter is breaking
    "REQ_PROP_ADDED_REQUIRED": ("breaking", "Changed", "op"),  # oasdiff new-required-request-property
    "REQ_PROP_ADDED_OPTIONAL": ("non-breaking", "Added", "field"),
    "REQ_PROP_BECAME_REQUIRED": ("breaking", "Changed", "op"),  # oasdiff request-property-became-required
    "REQ_PROP_BECAME_OPTIONAL": ("non-breaking", "Changed", "field"),
    "REQ_TYPE_CHANGED": ("breaking", "Changed", "field"),    # oasdiff request-body-type-changed
    "REQ_ENUM_NARROWED": ("breaking", "Changed", "field"),   # oasdiff request-property-enum-value-removed / became-enum
    "REQ_ENUM_WIDENED": ("non-breaking", "Changed", "field"),
    "RESP_PROP_REMOVED": ("breaking", "Removed", "field"),   # GitHub breaking; oasdiff: required removed breaking, optional removed info
    "RESP_PROP_ADDED": ("non-breaking", "Added", "field"),   # GitHub additive
    "RESP_TYPE_CHANGED": ("breaking", "Changed", "field"),   # oasdiff response-property-type-changed
    "RESP_ENUM_NARROWED": ("non-breaking", "Changed", "field"),  # oasdiff response-property-enum-value-removed = info
    "RESP_ENUM_WIDENED": ("non-breaking", "Changed", "field"),   # GitHub additive (oasdiff warns)
    "RESP_SUCCESS_STATUS_REMOVED": ("breaking", "Removed", "op"),  # oasdiff response-success-status-removed
    "RESP_STATUS_REMOVED": ("non-breaking", "Removed", "field"),  # oasdiff response-non-success-status-removed = info
    "RESP_STATUS_ADDED": ("non-breaking", "Added", "field"),
    "DOCS_CHANGED": ("docs-only", "Changed", "field"),
}
CATEGORIES = ["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"]


def esc(s):
    return str(s).replace("~", "~0").replace("/", "~1")


def unesc(s):
    return str(s).replace("~1", "/").replace("~0", "~")


def is_obj(x):
    return isinstance(x, dict)


def has(o, k):
    return is_obj(o) and k in o


def sorted_keys(a, b):
    ks = set()
    for o in (a, b):
        if is_obj(o):
            ks.update(o.keys())
    return sorted(ks)


def js(v):
    return json.dumps(v, separators=(",", ":"), ensure_ascii=False)


def val(v):
    return v if isinstance(v, str) else js(v)


def resolve(doc, node):
    r, guard = "", 0
    while is_obj(node) and isinstance(node.get("$ref"), str) and node["$ref"].startswith("#/") and guard < 32:
        r = node["$ref"]
        cur = doc
        for part in node["$ref"][2:].split("/"):
            cur = cur.get(unesc(part)) if is_obj(cur) else None
        node = cur
        guard += 1
    return node, r


def norm_type(s):
    t = s.get("type")
    t = list(t) if isinstance(t, list) else ([t] if isinstance(t, str) else [])
    if s.get("nullable") is True and t and "null" not in t:
        t.append("null")
    return "|".join(sorted(t))


def sec_key(reqs):
    if not isinstance(reqs, list) or not reqs:
        return "none"
    parts = []
    for r in reqs:
        if not is_obj(r) or not r:
            parts.append("anonymous")
            continue
        items = []
        for k in sorted(r.keys()):
            sc = sorted(r[k]) if isinstance(r[k], list) else []
            items.append(k + "[" + " ".join(sc) + "]" if sc else k)
        parts.append("+".join(items))
    return ", ".join(sorted(parts))


def json_media(content):
    if not is_obj(content):
        return None
    keys = sorted(content.keys())
    if "application/json" in keys:
        return "application/json"
    for k in keys:
        if "json" in k:
            return k
    return None


def diff(old, new):
    out = []

    def add(rule, op, ptr, name, detail):
        sev, cat, scope = RULES[rule]
        out.append({"rule": rule, "severity": sev, "category": cat, "scope": scope, "op": op,
                    "ptr": ptr, "name": str(name), "detail": detail})

    def schema(ctx, op, ptr, name, o_node, n_node, stack):
        o, oref = resolve(old, o_node)
        n, nref = resolve(new, n_node)
        if not is_obj(o) or not is_obj(n):
            return
        key = oref + ">" + nref
        if key != ">" and key in stack:
            return
        stack = stack + [key]
        R = "REQ_" if ctx == "request" else "RESP_"
        word = "request" if ctx == "request" else "response"
        ot, nt = norm_type(o), norm_type(n)
        if ot and nt and ot != nt:
            add(R + "TYPE_CHANGED", op, ptr, name, f"{word} field {name} type {ot} to {nt}")
        oe = o.get("enum") if isinstance(o.get("enum"), list) else None
        ne = n.get("enum") if isinstance(n.get("enum"), list) else None
        if oe is not None and ne is not None:
            ns = [js(v) for v in ne]
            os_ = [js(v) for v in oe]
            gone = [v for v in oe if js(v) not in ns]
            come = [v for v in ne if js(v) not in os_]
            if gone:
                add(R + "ENUM_NARROWED", op, ptr, name,
                    f"request field {name} no longer accepts " + ", ".join(val(v) for v in gone) if ctx == "request"
                    else f"response field {name} no longer returns " + ", ".join(val(v) for v in gone))
            if come:
                add(R + "ENUM_WIDENED", op, ptr, name,
                    f"request field {name} also accepts " + ", ".join(val(v) for v in come) if ctx == "request"
                    else f"response field {name} may now return " + ", ".join(val(v) for v in come))
        elif oe is None and ne is not None:
            add(R + "ENUM_NARROWED", op, ptr, name, f"{word} field {name} now limited to " + ", ".join(val(v) for v in ne))
        elif oe is not None and ne is None:
            add(R + "ENUM_WIDENED", op, ptr, name, f"{word} field {name} no longer limited to a list")
        if (o.get("description") or "") != (n.get("description") or ""):
            add("DOCS_CHANGED", op, ptr, name, f"description of {name} edited")
        op_ = o["properties"] if is_obj(o.get("properties")) else {}
        np_ = n["properties"] if is_obj(n.get("properties")) else {}
        oreq = o["required"] if isinstance(o.get("required"), list) else []
        nreq = n["required"] if isinstance(n.get("required"), list) else []
        for k in sorted_keys(op_, np_):
            cp = ptr + "/properties/" + esc(k)
            in_o, in_n = k in op_, k in np_
            if in_o and not in_n:
                add(R + "PROP_REMOVED", op, cp, k, f"{word} field {k} removed")
            elif not in_o and in_n:
                if ctx == "request":
                    if k in nreq:
                        add("REQ_PROP_ADDED_REQUIRED", op, cp, k, f"new required request field {k}")
                    else:
                        add("REQ_PROP_ADDED_OPTIONAL", op, cp, k, f"new optional request field {k}")
                else:
                    add("RESP_PROP_ADDED", op, cp, k, f"new response field {k}")
            else:
                if ctx == "request":
                    was_r, is_r = k in oreq, k in nreq
                    if not was_r and is_r:
                        add("REQ_PROP_BECAME_REQUIRED", op, cp, k, f"request field {k} is now required")
                    if was_r and not is_r:
                        add("REQ_PROP_BECAME_OPTIONAL", op, cp, k, f"request field {k} is now optional")
                schema(ctx, op, cp, k, op_[k], np_[k], stack)
        if "items" in o and "items" in n:
            schema(ctx, op, ptr + "/items", name, o["items"], n["items"], stack)

    def params(doc, path_item, op_obj):
        m = {}
        for lst in (path_item.get("parameters"), op_obj.get("parameters")):
            if not isinstance(lst, list):
                continue
            for p in lst:
                rp, _ = resolve(doc, p)
                if not is_obj(rp) or not isinstance(rp.get("name"), str):
                    continue
                loc = rp["in"] if "in" in rp else "undefined"
                m[f"{loc}:{rp['name']}"] = rp
        return m

    def operation(path, method, o_pi, n_pi, o, n):
        op = method.upper() + " " + path
        base = "/paths/" + esc(path) + "/" + method
        if (o.get("summary") or "") != (n.get("summary") or ""):
            add("DOCS_CHANGED", op, base + "/summary", "summary", "summary edited")
        if (o.get("description") or "") != (n.get("description") or ""):
            add("DOCS_CHANGED", op, base + "/description", "description", "description edited")
        if o.get("deprecated") is not True and n.get("deprecated") is True:
            add("OP_DEPRECATED", op, base + "/deprecated", op, "operation deprecated")
        os_ = o["security"] if "security" in o else old.get("security")
        ns_ = n["security"] if "security" in n else new.get("security")
        ok, nk = sec_key(os_), sec_key(ns_)
        if ok != nk:
            add("SECURITY_CHANGED", op, base + "/security", "security", f"auth changed from {ok} to {nk}")
        op_, np_ = params(old, o_pi, o), params(new, n_pi, n)
        for k in sorted_keys(op_, np_):
            loc, nm = k.split(":", 1)
            pp = base + "/parameters/" + esc(loc) + "/" + esc(nm)
            if k in op_ and k not in np_:
                add("PARAM_REMOVED", op, pp, nm, f"{loc} parameter {nm} removed")
            elif k not in op_ and k in np_:
                if np_[k].get("required") is True:
                    add("PARAM_ADDED_REQUIRED", op, pp, nm, f"new required {loc} parameter {nm}")
                else:
                    add("PARAM_ADDED_OPTIONAL", op, pp, nm, f"new optional {loc} parameter {nm}")
            else:
                a, b = op_[k], np_[k]
                if a.get("required") is not True and b.get("required") is True:
                    add("PARAM_BECAME_REQUIRED", op, pp, nm, f"{loc} parameter {nm} is now required")
                if a.get("required") is True and b.get("required") is not True:
                    add("PARAM_BECAME_OPTIONAL", op, pp, nm, f"{loc} parameter {nm} is now optional")
                if a.get("deprecated") is not True and b.get("deprecated") is True:
                    add("PARAM_DEPRECATED", op, pp, nm, f"{loc} parameter {nm} deprecated")
                if (a.get("description") or "") != (b.get("description") or ""):
                    add("DOCS_CHANGED", op, pp, nm, f"description of {loc} parameter {nm} edited")
                if "schema" in a and "schema" in b:
                    schema("request", op, pp + "/schema", nm, a["schema"], b["schema"], [])
        ob, _ = resolve(old, o.get("requestBody"))
        nb, _ = resolve(new, n.get("requestBody"))
        ob_req = is_obj(ob) and ob.get("required") is True
        nb_req = is_obj(nb) and nb.get("required") is True
        if not ob_req and nb_req:
            add("REQ_BODY_BECAME_REQUIRED", op, base + "/requestBody", "requestBody", "request body is now required")
        if is_obj(ob) and is_obj(nb):
            om, nm2 = json_media(ob.get("content")), json_media(nb.get("content"))
            if om and nm2 and om == nm2 and has(ob["content"][om], "schema") and has(nb["content"][nm2], "schema"):
                schema("request", op, base + "/requestBody/content/" + esc(om) + "/schema", "body",
                       ob["content"][om]["schema"], nb["content"][nm2]["schema"], [])
        orr = o["responses"] if is_obj(o.get("responses")) else {}
        nrr = n["responses"] if is_obj(n.get("responses")) else {}
        for code in sorted_keys(orr, nrr):
            rp = base + "/responses/" + esc(code)
            if code in orr and code not in nrr:
                if str(code)[:1] == "2":
                    add("RESP_SUCCESS_STATUS_REMOVED", op, rp, code, f"success response {code} removed")
                else:
                    add("RESP_STATUS_REMOVED", op, rp, code, f"response {code} removed")
            elif code not in orr and code in nrr:
                add("RESP_STATUS_ADDED", op, rp, code, f"new response {code}")
            else:
                a, _ = resolve(old, orr[code])
                b, _ = resolve(new, nrr[code])
                if not is_obj(a) or not is_obj(b):
                    continue
                if (a.get("description") or "") != (b.get("description") or ""):
                    add("DOCS_CHANGED", op, rp + "/description", code, f"description of response {code} edited")
                am, bm = json_media(a.get("content")), json_media(b.get("content"))
                if am and bm and am == bm and has(a["content"][am], "schema") and has(b["content"][bm], "schema"):
                    schema("response", op, rp + "/content/" + esc(am) + "/schema", code,
                           a["content"][am]["schema"], b["content"][bm]["schema"], [])

    o_p = old["paths"] if is_obj(old.get("paths")) else {}
    n_p = new["paths"] if is_obj(new.get("paths")) else {}
    for path in sorted_keys(o_p, n_p):
        a, _ = resolve(old, o_p.get(path))
        b, _ = resolve(new, n_p.get(path))
        for m in METHODS:
            in_a = is_obj(a) and is_obj(a.get(m))
            in_b = is_obj(b) and is_obj(b.get(m))
            op = m.upper() + " " + path
            ptr = "/paths/" + esc(path) + "/" + m
            if in_a and not in_b:
                add("OP_REMOVED", op, ptr, op, "operation removed")
            elif not in_a and in_b:
                add("OP_ADDED", op, ptr, op, "new operation")
            elif in_a and in_b:
                operation(path, m, a, b, a[m], b[m])
    out.sort(key=lambda c: (c["ptr"], c["rule"], c["detail"]))
    return out


def parse_ver(v):
    import re
    m = re.match(r"^v?(\d+)\.(\d+)\.(\d+)", str(v or ""))
    return [int(m.group(1)), int(m.group(2)), int(m.group(3))] if m else [0, 0, 0]


def required(changes):
    sev = [c["severity"] for c in changes]
    return "major" if "breaking" in sev else "minor" if "non-breaking" in sev else "patch" if sev else "none"


def bump_version(v, level):
    p = parse_ver(v)
    if level == "major":
        return f"{p[0] + 1}.0.0"
    if level == "minor":
        return f"{p[0]}.{p[1] + 1}.0"
    if level == "patch":
        return f"{p[0]}.{p[1]}.{p[2] + 1}"
    return ".".join(str(x) for x in p)


def counts(changes):
    c = {"breaking": 0, "non-breaking": 0, "docs-only": 0, "total": len(changes)}
    for x in changes:
        c[x["severity"]] += 1
    return c


def changelog(changes, version, date):
    lines = [f"## [{version}] - {date}"]
    for cat in CATEGORIES:
        groups, order = {}, []
        for c in changes:
            if c["category"] != cat:
                continue
            tag = "**BREAKING** " if c["severity"] == "breaking" else ""
            tail = " (docs only)" if c["severity"] == "docs-only" else ""
            k = tag + c["detail"] + tail
            if k not in groups:
                groups[k] = []
                order.append(k)
            if c["op"] not in groups[k]:
                groups[k].append(c["op"])
        if not order:
            continue
        lines.append("### " + cat)
        order.sort(key=lambda k: (0 if k.startswith("**BREAKING**") else 1, k))
        for k in order:
            lines.append("- " + k + " (" + "; ".join(sorted(groups[k])) + ")")
    return "\n".join(lines)


def impact(changes, consumers):
    res = []
    for c in consumers:
        hits = []
        for x in changes:
            if x["severity"] != "breaking":
                continue
            for u in c["uses"]:
                if u["op"] != x["op"]:
                    continue
                if x["scope"] == "op" or x["name"] in u["fields"]:
                    h = x["op"] + ": " + x["detail"]
                    if h not in hits:
                        hits.append(h)
        res.append({"id": c["id"], "name": c["name"], "broken": bool(hits), "hits": sorted(hits)})
    return res


def run(old, new, ship="honest", date="YYYY-MM-DD", consumers=None):
    changes = diff(old, new)
    req = required(changes)
    shipped = "minor" if ship == "minor" and req == "major" else req
    old_v = (old.get("info") or {}).get("version")
    version = bump_version(old_v, shipped)
    res = {"changes": changes, "counts": counts(changes), "required": req, "shipped": shipped,
           "fromVersion": str(old_v or ""), "version": version,
           "changelog": changelog(changes, version, date), "consumers": None}
    if consumers:
        imp = impact(changes, consumers)
        hit = sum(1 for c in imp if c["broken"])
        res["consumers"] = {"list": imp, "total": len(imp), "hit": hit,
                            "silent": 0 if shipped == "major" else hit,
                            "warned": hit if shipped == "major" else 0}
    return res


def load_sample():
    txt = (ROOT / "assets/adc-sample.js").read_text()
    start = txt.index("window.ADC_SAMPLE = ") + len("window.ADC_SAMPLE = ")
    return json.loads(txt[start:txt.rindex(";")])


def ladder():
    S = load_sample()
    out = {}
    for p in S["presets"]:
        for ship in ("honest", "minor"):
            out[p["id"] + "/" + ship] = run(p["old"], p["new"], ship, p["date"], S["consumers"] if p["consumers"] else None)
    return out


# ------------------------------------------------------------------ unit tests
def base_doc():
    return {
        "openapi": "3.1.0", "info": {"title": "t", "version": "1.0.0"},
        "security": [{"key": []}],
        "paths": {"/things": {
            "get": {"summary": "List", "description": "d",
                    "parameters": [{"name": "page", "in": "query", "required": False, "schema": {"type": "integer"}},
                                   {"name": "kind", "in": "query", "required": False,
                                    "schema": {"type": "string", "enum": ["a", "b"]}}],
                    "responses": {"200": {"description": "ok", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Thing"}}}},
                                  "404": {"description": "missing"}}},
            "post": {"requestBody": {"required": True, "content": {"application/json": {"schema": {
                "type": "object", "required": ["name"],
                "properties": {"name": {"type": "string"}, "note": {"type": "string"},
                               "size": {"type": "string", "enum": ["s", "m", "l"]}}}}}},
                     "responses": {"201": {"description": "made"}}}}},
        "components": {"schemas": {"Thing": {"type": "object", "required": ["id"], "properties": {
            "id": {"type": "string"}, "label": {"type": "string"},
            "state": {"type": "string", "enum": ["on", "off"]}}}}},
    }


def mutate(fn):
    d = base_doc()
    fn(d)
    return d


G = lambda d: d["paths"]["/things"]["get"]
P = lambda d: d["paths"]["/things"]["post"]
PB = lambda d: P(d)["requestBody"]["content"]["application/json"]["schema"]
T = lambda d: d["components"]["schemas"]["Thing"]

# (rule, description, mutation that MUST fire it, near-miss mutation that must NOT fire it)
TESTS = [
    ("OP_REMOVED", "delete GET", lambda d: d["paths"]["/things"].pop("get"), lambda d: G(d).update(deprecated=True)),
    ("OP_ADDED", "add DELETE", lambda d: d["paths"]["/things"].update(delete={"responses": {"204": {"description": "x"}}}), lambda d: G(d).update(summary="List all")),
    ("OP_DEPRECATED", "deprecate GET", lambda d: G(d).update(deprecated=True), lambda d: G(d).update(deprecated=False)),
    ("SECURITY_CHANGED", "bearer instead of key", lambda d: G(d).update(security=[{"bearer": []}]), lambda d: G(d).update(security=[{"key": []}])),
    ("PARAM_REMOVED", "drop page", lambda d: G(d)["parameters"].pop(0), lambda d: G(d)["parameters"][0].update(description="Page")),
    ("PARAM_ADDED_REQUIRED", "add required q", lambda d: G(d)["parameters"].append({"name": "q", "in": "query", "required": True, "schema": {"type": "string"}}),
     lambda d: G(d)["parameters"].append({"name": "q", "in": "query", "required": False, "schema": {"type": "string"}})),
    ("PARAM_ADDED_OPTIONAL", "add optional q", lambda d: G(d)["parameters"].append({"name": "q", "in": "query", "schema": {"type": "string"}}),
     lambda d: G(d)["parameters"].append({"name": "q", "in": "query", "required": True, "schema": {"type": "string"}})),
    ("PARAM_BECAME_REQUIRED", "page required", lambda d: G(d)["parameters"][0].update(required=True), lambda d: G(d)["parameters"][0].update(required=False)),
    ("PARAM_DEPRECATED", "page deprecated", lambda d: G(d)["parameters"][0].update(deprecated=True), lambda d: G(d)["parameters"][0].update(deprecated=False)),
    ("REQ_PROP_REMOVED", "drop note", lambda d: PB(d)["properties"].pop("note"), lambda d: PB(d)["properties"]["note"].update(description="n")),
    ("REQ_PROP_ADDED_REQUIRED", "add required email", lambda d: (PB(d)["properties"].update(email={"type": "string"}), PB(d)["required"].append("email")),
     lambda d: PB(d)["properties"].update(email={"type": "string"})),
    ("REQ_PROP_ADDED_OPTIONAL", "add optional email", lambda d: PB(d)["properties"].update(email={"type": "string"}),
     lambda d: (PB(d)["properties"].update(email={"type": "string"}), PB(d)["required"].append("email"))),
    ("REQ_PROP_BECAME_REQUIRED", "note required", lambda d: PB(d)["required"].append("note"), lambda d: PB(d)["properties"]["note"].update(minLength=1)),
    ("REQ_PROP_BECAME_OPTIONAL", "name optional", lambda d: PB(d)["required"].remove("name"), lambda d: PB(d)["required"].append("note")),
    ("REQ_TYPE_CHANGED", "note integer", lambda d: PB(d)["properties"]["note"].update(type="integer"), lambda d: PB(d)["properties"]["note"].update(format="uri")),
    ("REQ_ENUM_NARROWED", "size loses l", lambda d: PB(d)["properties"]["size"].update(enum=["s", "m"]), lambda d: PB(d)["properties"]["size"].update(enum=["s", "m", "l", "xl"])),
    ("REQ_ENUM_WIDENED", "size gains xl", lambda d: PB(d)["properties"]["size"].update(enum=["s", "m", "l", "xl"]), lambda d: PB(d)["properties"]["size"].update(enum=["l", "m", "s"])),
    ("RESP_PROP_REMOVED", "drop label", lambda d: T(d)["properties"].pop("label"), lambda d: T(d)["properties"]["label"].update(maxLength=40)),
    ("RESP_PROP_ADDED", "add colour", lambda d: T(d)["properties"].update(colour={"type": "string"}), lambda d: T(d)["properties"]["label"].update(maxLength=40)),
    ("RESP_TYPE_CHANGED", "id integer", lambda d: T(d)["properties"]["id"].update(type="integer"), lambda d: T(d)["properties"]["id"].update(type=["string"])),
    ("RESP_ENUM_NARROWED", "state loses off", lambda d: T(d)["properties"]["state"].update(enum=["on"]), lambda d: T(d)["properties"]["state"].update(enum=["on", "off", "idle"])),
    ("RESP_ENUM_WIDENED", "state gains idle", lambda d: T(d)["properties"]["state"].update(enum=["on", "off", "idle"]), lambda d: T(d)["properties"]["state"].update(enum=["off", "on"])),
    ("RESP_SUCCESS_STATUS_REMOVED", "201 becomes 202", lambda d: P(d).update(responses={"202": {"description": "made"}}),
     lambda d: G(d)["responses"].pop("404")),
    ("RESP_STATUS_REMOVED", "404 dropped", lambda d: G(d)["responses"].pop("404"), lambda d: G(d)["responses"]["404"].update(description="gone")),
    ("RESP_STATUS_ADDED", "429 added", lambda d: G(d)["responses"].update({"429": {"description": "slow down"}}), lambda d: G(d)["responses"]["404"].update(description="gone")),
    ("DOCS_CHANGED", "summary edit", lambda d: G(d).update(summary="List every thing"), lambda d: G(d).update(summary="List")),
]


def special_pairs():
    """Rules whose PASS case needs a different OLD document."""
    pairs = []
    # PARAM_BECAME_OPTIONAL: old has page required, new optional
    o = mutate(lambda d: G(d)["parameters"][0].update(required=True))
    pairs.append(("PARAM_BECAME_OPTIONAL", "page optional again", o, base_doc(), True))
    pairs.append(("PARAM_BECAME_OPTIONAL", "page stays required", o, copy.deepcopy(o), False))
    # REQ_BODY_BECAME_REQUIRED: old body optional, new required
    o = mutate(lambda d: P(d)["requestBody"].update(required=False))
    pairs.append(("REQ_BODY_BECAME_REQUIRED", "body now required", o, base_doc(), True))
    pairs.append(("REQ_BODY_BECAME_REQUIRED", "body stays optional", o, copy.deepcopy(o), False))
    # 3.0 nullable equals 3.1 type array: no type change
    o = mutate(lambda d: T(d)["properties"]["label"].update(nullable=True))
    n = mutate(lambda d: T(d)["properties"]["label"].update(type=["string", "null"]))
    pairs.append(("RESP_TYPE_CHANGED", "nullable:true == type [string,null]", o, n, False))
    return pairs


def all_tests():
    cases = []
    for rule, desc, fire, miss in TESTS:
        cases.append({"rule": rule, "desc": desc, "old": base_doc(), "new": mutate(fire), "fires": True})
        cases.append({"rule": rule, "desc": desc + " (near miss)", "old": base_doc(), "new": mutate(miss), "fires": False})
    for rule, desc, o, n, fires in special_pairs():
        cases.append({"rule": rule, "desc": desc, "old": o, "new": n, "fires": fires})
    return cases


def test():
    cases = all_tests()
    fails = 0
    for c in cases:
        got = any(x["rule"] == c["rule"] for x in diff(c["old"], c["new"]))
        ok = got == c["fires"]
        fails += not ok
        print(("PASS" if ok else "FAIL"), c["rule"], "-", c["desc"])
    covered = {c["rule"] for c in cases if c["fires"]}
    missing = sorted(set(RULES) - covered)
    print(f"{len(cases) - fails}/{len(cases)} cases pass; rules with a firing test: {len(covered)}/{len(RULES)}; missing: {missing}")
    (ROOT / "materials/adc_rule_tests.json").write_text(json.dumps(cases, separators=(",", ":")))
    return 1 if fails or missing else 0


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "test"
    if cmd == "test":
        sys.exit(test())
    elif cmd == "ladder":
        print(json.dumps(ladder(), indent=1, sort_keys=True))
