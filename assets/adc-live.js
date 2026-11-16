/* adc-live.js - the changelog checker for learn-api-docs-changelogs-with-phoebe, by Phoebe Fu.
   A real OpenAPI diff engine: it compares two OpenAPI documents (JSON), classifies every change as
   breaking / non-breaking / docs-only with the rule table below, works out the SemVer bump and
   drafts a Keep a Changelog entry. The Python twin is materials/adc_reference.py; both must print
   the same change list on every preset (materials/compare-ladder.py checks it).
   The consumer list is constructed and the "who breaks" panel is a simulation; the diff is not.
   No dependencies. Runs in the browser and in node (module.exports). */
(function (root) {
  "use strict";

  var METHODS = ["get", "put", "post", "delete", "options", "head", "patch", "trace"];

  // rule id: [severity, Keep a Changelog category, scope]. scope "op" = hits every caller of the
  // operation; "field" = hits only callers that use the named field, parameter or status.
  var RULES = {
    OP_REMOVED: ["breaking", "Removed", "op"],
    OP_ADDED: ["non-breaking", "Added", "op"],
    OP_DEPRECATED: ["non-breaking", "Deprecated", "op"],
    SECURITY_CHANGED: ["breaking", "Changed", "op"],
    PARAM_REMOVED: ["breaking", "Removed", "field"],
    PARAM_ADDED_REQUIRED: ["breaking", "Changed", "op"],
    PARAM_ADDED_OPTIONAL: ["non-breaking", "Added", "field"],
    PARAM_BECAME_REQUIRED: ["breaking", "Changed", "op"],
    PARAM_BECAME_OPTIONAL: ["non-breaking", "Changed", "field"],
    PARAM_DEPRECATED: ["non-breaking", "Deprecated", "field"],
    REQ_BODY_BECAME_REQUIRED: ["breaking", "Changed", "op"],
    REQ_PROP_REMOVED: ["breaking", "Removed", "field"],
    REQ_PROP_ADDED_REQUIRED: ["breaking", "Changed", "op"],
    REQ_PROP_ADDED_OPTIONAL: ["non-breaking", "Added", "field"],
    REQ_PROP_BECAME_REQUIRED: ["breaking", "Changed", "op"],
    REQ_PROP_BECAME_OPTIONAL: ["non-breaking", "Changed", "field"],
    REQ_TYPE_CHANGED: ["breaking", "Changed", "field"],
    REQ_ENUM_NARROWED: ["breaking", "Changed", "field"],
    REQ_ENUM_WIDENED: ["non-breaking", "Changed", "field"],
    RESP_PROP_REMOVED: ["breaking", "Removed", "field"],
    RESP_PROP_ADDED: ["non-breaking", "Added", "field"],
    RESP_TYPE_CHANGED: ["breaking", "Changed", "field"],
    RESP_ENUM_NARROWED: ["non-breaking", "Changed", "field"],
    RESP_ENUM_WIDENED: ["non-breaking", "Changed", "field"],
    RESP_SUCCESS_STATUS_REMOVED: ["breaking", "Removed", "op"],
    RESP_STATUS_REMOVED: ["non-breaking", "Removed", "field"],
    RESP_STATUS_ADDED: ["non-breaking", "Added", "field"],
    DOCS_CHANGED: ["docs-only", "Changed", "field"]
  };
  var CATEGORIES = ["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"];

  function esc(s) { return String(s).replace(/~/g, "~0").replace(/\//g, "~1"); }
  function unesc(s) { return String(s).replace(/~1/g, "/").replace(/~0/g, "~"); }
  function isObj(x) { return x !== null && typeof x === "object" && !Array.isArray(x); }
  function has(o, k) { return isObj(o) && Object.prototype.hasOwnProperty.call(o, k); }
  function sortedKeys(a, b) {
    var seen = {}, out = [];
    [a, b].forEach(function (o) {
      if (isObj(o)) Object.keys(o).forEach(function (k) { if (!seen[k]) { seen[k] = 1; out.push(k); } });
    });
    return out.sort(cmp);
  }
  function cmp(a, b) { return a < b ? -1 : a > b ? 1 : 0; }
  function val(v) { return typeof v === "string" ? v : JSON.stringify(v); }

  // follow a local $ref chain; returns [node, refString or ""]
  function resolve(doc, node) {
    var r = "", guard = 0;
    while (isObj(node) && typeof node.$ref === "string" && node.$ref.indexOf("#/") === 0 && guard < 32) {
      r = node.$ref;
      var parts = node.$ref.slice(2).split("/"), cur = doc;
      for (var i = 0; i < parts.length; i++) cur = isObj(cur) ? cur[unesc(parts[i])] : undefined;
      node = cur; guard++;
    }
    return [node, r];
  }

  function normType(s) {
    var t = [];
    if (Array.isArray(s.type)) t = s.type.slice();
    else if (typeof s.type === "string") t = [s.type];
    if (s.nullable === true && t.length && t.indexOf("null") < 0) t.push("null");
    return t.sort(cmp).join("|");
  }

  function secKey(reqs) {
    if (!Array.isArray(reqs) || !reqs.length) return "none";
    return reqs.map(function (r) {
      if (!isObj(r) || !Object.keys(r).length) return "anonymous";
      return Object.keys(r).sort(cmp).map(function (k) {
        var sc = Array.isArray(r[k]) ? r[k].slice().sort(cmp) : [];
        return sc.length ? k + "[" + sc.join(" ") + "]" : k;
      }).join("+");
    }).sort(cmp).join(", ");
  }

  function jsonMedia(content) {
    if (!isObj(content)) return null;
    var keys = Object.keys(content).sort(cmp);
    if (keys.indexOf("application/json") >= 0) return "application/json";
    for (var i = 0; i < keys.length; i++) if (keys[i].indexOf("json") >= 0) return keys[i];
    return null;
  }

  function diff(oldDoc, newDoc) {
    var out = [];
    function add(rule, op, ptr, name, detail) {
      var r = RULES[rule];
      out.push({ rule: rule, severity: r[0], category: r[1], scope: r[2], op: op, ptr: ptr, name: String(name), detail: detail });
    }

    function schema(ctx, op, ptr, name, oNode, nNode, stack) {
      var ro = resolve(oldDoc, oNode), rn = resolve(newDoc, nNode);
      var o = ro[0], n = rn[0];
      if (!isObj(o) || !isObj(n)) return;
      var key = ro[1] + ">" + rn[1];
      if (key !== ">" && stack.indexOf(key) >= 0) return;
      stack = stack.concat([key]);
      var R = ctx === "request" ? "REQ_" : "RESP_", word = ctx === "request" ? "request" : "response";
      var ot = normType(o), nt = normType(n);
      if (ot && nt && ot !== nt) add(R + "TYPE_CHANGED", op, ptr, name, word + " field " + name + " type " + ot + " to " + nt);
      var oe = Array.isArray(o.enum) ? o.enum : null, ne = Array.isArray(n.enum) ? n.enum : null;
      if (oe && ne) {
        var ns = ne.map(JSON.stringify), os = oe.map(JSON.stringify);
        var gone = oe.filter(function (v) { return ns.indexOf(JSON.stringify(v)) < 0; });
        var come = ne.filter(function (v) { return os.indexOf(JSON.stringify(v)) < 0; });
        if (gone.length) add(R + "ENUM_NARROWED", op, ptr, name, ctx === "request"
          ? "request field " + name + " no longer accepts " + gone.map(val).join(", ")
          : "response field " + name + " no longer returns " + gone.map(val).join(", "));
        if (come.length) add(R + "ENUM_WIDENED", op, ptr, name, ctx === "request"
          ? "request field " + name + " also accepts " + come.map(val).join(", ")
          : "response field " + name + " may now return " + come.map(val).join(", "));
      } else if (!oe && ne) {
        add(R + "ENUM_NARROWED", op, ptr, name, word + " field " + name + " now limited to " + ne.map(val).join(", "));
      } else if (oe && !ne) {
        add(R + "ENUM_WIDENED", op, ptr, name, word + " field " + name + " no longer limited to a list");
      }
      if ((o.description || "") !== (n.description || ""))
        add("DOCS_CHANGED", op, ptr, name, "description of " + name + " edited");
      var op_ = isObj(o.properties) ? o.properties : {}, np = isObj(n.properties) ? n.properties : {};
      var oreq = Array.isArray(o.required) ? o.required : [], nreq = Array.isArray(n.required) ? n.required : [];
      sortedKeys(op_, np).forEach(function (k) {
        var cp = ptr + "/properties/" + esc(k);
        var inO = has(op_, k), inN = has(np, k);
        if (inO && !inN) add(R + "PROP_REMOVED", op, cp, k, word + " field " + k + " removed");
        else if (!inO && inN) {
          if (ctx === "request") {
            if (nreq.indexOf(k) >= 0) add("REQ_PROP_ADDED_REQUIRED", op, cp, k, "new required request field " + k);
            else add("REQ_PROP_ADDED_OPTIONAL", op, cp, k, "new optional request field " + k);
          } else add("RESP_PROP_ADDED", op, cp, k, "new response field " + k);
        } else {
          if (ctx === "request") {
            var wasR = oreq.indexOf(k) >= 0, isR = nreq.indexOf(k) >= 0;
            if (!wasR && isR) add("REQ_PROP_BECAME_REQUIRED", op, cp, k, "request field " + k + " is now required");
            if (wasR && !isR) add("REQ_PROP_BECAME_OPTIONAL", op, cp, k, "request field " + k + " is now optional");
          }
          schema(ctx, op, cp, k, op_[k], np[k], stack);
        }
      });
      if (has(o, "items") && has(n, "items")) schema(ctx, op, ptr + "/items", name, o.items, n.items, stack);
    }

    function params(doc, pathItem, opObj) {
      var m = {}, order = [];
      [pathItem.parameters, opObj.parameters].forEach(function (list) {
        if (!Array.isArray(list)) return;
        list.forEach(function (p) {
          var rp = resolve(doc, p)[0];
          if (!isObj(rp) || typeof rp.name !== "string") return;
          var k = rp["in"] + ":" + rp.name;
          if (!m[k]) order.push(k);
          m[k] = { node: p, res: rp };
        });
      });
      return m;
    }

    function operation(path, method, oPI, nPI, o, n) {
      var op = method.toUpperCase() + " " + path;
      var base = "/paths/" + esc(path) + "/" + method;
      if ((o.summary || "") !== (n.summary || "")) add("DOCS_CHANGED", op, base + "/summary", "summary", "summary edited");
      if ((o.description || "") !== (n.description || "")) add("DOCS_CHANGED", op, base + "/description", "description", "description edited");
      if (o.deprecated !== true && n.deprecated === true) add("OP_DEPRECATED", op, base + "/deprecated", op, "operation deprecated");
      var os = has(o, "security") ? o.security : oldDoc.security, ns = has(n, "security") ? n.security : newDoc.security;
      var oK = secKey(os), nK = secKey(ns);
      if (oK !== nK) add("SECURITY_CHANGED", op, base + "/security", "security", "auth changed from " + oK + " to " + nK);
      // parameters
      var op_ = params(oldDoc, oPI, o), np = params(newDoc, nPI, n);
      sortedKeys(op_, np).forEach(function (k) {
        var parts = k.split(":"), loc = parts[0], nm = parts.slice(1).join(":");
        var pp = base + "/parameters/" + esc(loc) + "/" + esc(nm);
        if (op_[k] && !np[k]) add("PARAM_REMOVED", op, pp, nm, loc + " parameter " + nm + " removed");
        else if (!op_[k] && np[k]) {
          if (np[k].res.required === true) add("PARAM_ADDED_REQUIRED", op, pp, nm, "new required " + loc + " parameter " + nm);
          else add("PARAM_ADDED_OPTIONAL", op, pp, nm, "new optional " + loc + " parameter " + nm);
        } else {
          var a = op_[k].res, b = np[k].res;
          if (a.required !== true && b.required === true) add("PARAM_BECAME_REQUIRED", op, pp, nm, loc + " parameter " + nm + " is now required");
          if (a.required === true && b.required !== true) add("PARAM_BECAME_OPTIONAL", op, pp, nm, loc + " parameter " + nm + " is now optional");
          if (a.deprecated !== true && b.deprecated === true) add("PARAM_DEPRECATED", op, pp, nm, loc + " parameter " + nm + " deprecated");
          if ((a.description || "") !== (b.description || "")) add("DOCS_CHANGED", op, pp, nm, "description of " + loc + " parameter " + nm + " edited");
          if (has(a, "schema") && has(b, "schema")) schema("request", op, pp + "/schema", nm, a.schema, b.schema, []);
        }
      });
      // request body
      var ob = resolve(oldDoc, o.requestBody)[0], nb = resolve(newDoc, n.requestBody)[0];
      var obReq = isObj(ob) && ob.required === true, nbReq = isObj(nb) && nb.required === true;
      if (!obReq && nbReq) add("REQ_BODY_BECAME_REQUIRED", op, base + "/requestBody", "requestBody", "request body is now required");
      if (isObj(ob) && isObj(nb)) {
        var om = jsonMedia(ob.content), nm2 = jsonMedia(nb.content);
        if (om && nm2 && om === nm2 && has(ob.content[om], "schema") && has(nb.content[nm2], "schema"))
          schema("request", op, base + "/requestBody/content/" + esc(om) + "/schema", "body", ob.content[om].schema, nb.content[nm2].schema, []);
      }
      // responses
      var orr = isObj(o.responses) ? o.responses : {}, nrr = isObj(n.responses) ? n.responses : {};
      sortedKeys(orr, nrr).forEach(function (code) {
        var rp = base + "/responses/" + esc(code);
        if (has(orr, code) && !has(nrr, code)) {
          if (String(code).charAt(0) === "2") add("RESP_SUCCESS_STATUS_REMOVED", op, rp, code, "success response " + code + " removed");
          else add("RESP_STATUS_REMOVED", op, rp, code, "response " + code + " removed");
        } else if (!has(orr, code) && has(nrr, code)) add("RESP_STATUS_ADDED", op, rp, code, "new response " + code);
        else {
          var a = resolve(oldDoc, orr[code])[0], b = resolve(newDoc, nrr[code])[0];
          if (!isObj(a) || !isObj(b)) return;
          if ((a.description || "") !== (b.description || "")) add("DOCS_CHANGED", op, rp + "/description", code, "description of response " + code + " edited");
          var am = jsonMedia(a.content), bm = jsonMedia(b.content);
          if (am && bm && am === bm && has(a.content[am], "schema") && has(b.content[bm], "schema"))
            schema("response", op, rp + "/content/" + esc(am) + "/schema", code, a.content[am].schema, b.content[bm].schema, []);
        }
      });
    }

    var oP = isObj(oldDoc.paths) ? oldDoc.paths : {}, nP = isObj(newDoc.paths) ? newDoc.paths : {};
    sortedKeys(oP, nP).forEach(function (path) {
      var a = resolve(oldDoc, oP[path])[0], b = resolve(newDoc, nP[path])[0];
      METHODS.forEach(function (m) {
        var inA = isObj(a) && isObj(a[m]), inB = isObj(b) && isObj(b[m]);
        var op = m.toUpperCase() + " " + path, ptr = "/paths/" + esc(path) + "/" + m;
        if (inA && !inB) add("OP_REMOVED", op, ptr, op, "operation removed");
        else if (!inA && inB) add("OP_ADDED", op, ptr, op, "new operation");
        else if (inA && inB) operation(path, m, a, b, a[m], b[m]);
      });
    });
    out.sort(function (x, y) { return cmp(x.ptr, y.ptr) || cmp(x.rule, y.rule) || cmp(x.detail, y.detail); });
    return out;
  }

  function parseVer(v) {
    var m = /^v?(\d+)\.(\d+)\.(\d+)/.exec(String(v || ""));
    return m ? [parseInt(m[1], 10), parseInt(m[2], 10), parseInt(m[3], 10)] : [0, 0, 0];
  }
  function required(changes) {
    var b = 0, nb = 0, d = 0;
    changes.forEach(function (c) { if (c.severity === "breaking") b++; else if (c.severity === "non-breaking") nb++; else d++; });
    return b ? "major" : nb ? "minor" : d ? "patch" : "none";
  }
  function bumpVersion(v, level) {
    var p = parseVer(v);
    if (level === "major") return (p[0] + 1) + ".0.0";
    if (level === "minor") return p[0] + "." + (p[1] + 1) + ".0";
    if (level === "patch") return p[0] + "." + p[1] + "." + (p[2] + 1);
    return p.join(".");
  }
  function counts(changes) {
    var c = { breaking: 0, "non-breaking": 0, "docs-only": 0, total: changes.length };
    changes.forEach(function (x) { c[x.severity]++; });
    return c;
  }

  // Keep a Changelog entry; identical details across operations are merged into one line.
  function changelog(changes, version, date) {
    var lines = ["## [" + version + "] - " + date];
    CATEGORIES.forEach(function (cat) {
      var groups = {}, order = [];
      changes.forEach(function (c) {
        if (c.category !== cat) return;
        var tag = c.severity === "breaking" ? "**BREAKING** " : "";
        var tail = c.severity === "docs-only" ? " (docs only)" : "";
        var k = tag + c.detail + tail;
        if (!groups[k]) { groups[k] = []; order.push(k); }
        if (groups[k].indexOf(c.op) < 0) groups[k].push(c.op);
      });
      if (!order.length) return;
      lines.push("### " + cat);
      order.sort(function (a, b) {
        var ab = a.indexOf("**BREAKING**") === 0 ? 0 : 1, bb = b.indexOf("**BREAKING**") === 0 ? 0 : 1;
        return (ab - bb) || cmp(a, b);
      });
      order.forEach(function (k) { lines.push("- " + k + " (" + groups[k].sort(cmp).join("; ") + ")"); });
    });
    return lines.join("\n");
  }

  function impact(changes, consumers) {
    return consumers.map(function (c) {
      var hits = [];
      changes.forEach(function (x) {
        if (x.severity !== "breaking") return;
        c.uses.forEach(function (u) {
          if (u.op !== x.op) return;
          if (x.scope === "op" || u.fields.indexOf(x.name) >= 0) {
            var h = x.op + ": " + x.detail;
            if (hits.indexOf(h) < 0) hits.push(h);
          }
        });
      });
      return { id: c.id, name: c.name, broken: hits.length > 0, hits: hits.sort(cmp) };
    });
  }

  // One full run. ship: "honest" (the bump SemVer requires) or "minor" (the anti-lever).
  function run(oldDoc, newDoc, opts) {
    opts = opts || {};
    var changes = diff(oldDoc, newDoc);
    var req = required(changes);
    var shipped = opts.ship === "minor" && req === "major" ? "minor" : req;
    var oldV = oldDoc.info && oldDoc.info.version;
    var version = bumpVersion(oldV, shipped);
    var res = {
      changes: changes, counts: counts(changes), required: req, shipped: shipped,
      fromVersion: String(oldV || ""), version: version,
      changelog: changelog(changes, version, opts.date || "YYYY-MM-DD"), consumers: null
    };
    if (opts.consumers) {
      var imp = impact(changes, opts.consumers), hit = imp.filter(function (c) { return c.broken; }).length;
      res.consumers = {
        list: imp, total: imp.length, hit: hit,
        silent: shipped === "major" ? 0 : hit,
        warned: shipped === "major" ? hit : 0
      };
    }
    return res;
  }

  var ENGINE = { RULES: RULES, diff: diff, required: required, bumpVersion: bumpVersion, changelog: changelog, impact: impact, run: run, counts: counts };
  if (typeof module !== "undefined" && module.exports) { module.exports = ENGINE; return; }
  root.ADC = ENGINE;

  /* ------------------------------ the widget ------------------------------ */
  function h(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
  }

  function mount(host) {
    var S = root.ADC_SAMPLE;
    if (!S) { host.textContent = "Bench data did not load."; return; }
    var state = { preset: host.getAttribute("data-preset") || "pp-major", ship: host.getAttribute("data-ship") || "honest", custom: false, last: null };
    var lock = host.getAttribute("data-lock") === "1";
    host.innerHTML = "";
    var head = h("div", "adc-head");
    head.appendChild(h("h4", null, "The changelog checker"));
    head.appendChild(h("p", "adc-rail", "Real diff engine, running in this page: two OpenAPI documents in, every change classified, the SemVer bump and a Keep a Changelog draft out. JSON only (no YAML parser is loaded). Compares paths, operations, parameters, request bodies, JSON responses and auth; not webhooks, callbacks, links or response headers. Parcelpoint is a constructed example; the consumer list is constructed and the breakage panel is simulated."));
    host.appendChild(head);

    var presetRow = h("div", "adc-presets");
    if (!lock) {
      S.presets.forEach(function (p) {
        var b = h("button", "adc-preset", p.label);
        b.type = "button"; b.setAttribute("data-id", p.id);
        b.addEventListener("click", function () { load(p.id); });
        presetRow.appendChild(b);
      });
      host.appendChild(presetRow);
    }
    var note = h("p", "adc-note");
    host.appendChild(note);

    var ed = h("details", "adc-editors");
    ed.appendChild(h("summary", null, "Edit the two documents (JSON)"));
    var cols = h("div", "adc-cols");
    var taO = h("textarea", "adc-text"), taN = h("textarea", "adc-text");
    taO.setAttribute("aria-label", "Old OpenAPI document, JSON"); taN.setAttribute("aria-label", "New OpenAPI document, JSON");
    taO.spellcheck = false; taN.spellcheck = false;
    var cO = h("div"), cN = h("div");
    cO.appendChild(h("span", "adc-clabel", "Old (published)")); cO.appendChild(taO);
    cN.appendChild(h("span", "adc-clabel", "New (about to ship)")); cN.appendChild(taN);
    cols.appendChild(cO); cols.appendChild(cN); ed.appendChild(cols);
    var runBtn = h("button", "adc-run", "Run the diff"); runBtn.type = "button";
    ed.appendChild(runBtn);
    var err = h("p", "adc-err"); ed.appendChild(err);
    host.appendChild(ed);

    var ship = h("div", "adc-ship");
    var bH = h("button", "adc-shipbtn", "Ship the bump SemVer requires"); bH.type = "button"; bH.setAttribute("data-ship", "honest");
    var bM = h("button", "adc-shipbtn adc-trap", "Ship it as a minor"); bM.type = "button"; bM.setAttribute("data-ship", "minor");
    [bH, bM].forEach(function (b) { b.addEventListener("click", function () { state.ship = b.getAttribute("data-ship"); render(); }); ship.appendChild(b); });
    host.appendChild(ship);

    var headline = h("div", "adc-headline"); host.appendChild(headline);
    var cons = h("div", "adc-consumers"); host.appendChild(cons);
    var tableWrap = h("div", "adc-tablewrap"); host.appendChild(tableWrap);
    host.appendChild(h("span", "adc-clabel", "Drafted changelog entry (Keep a Changelog 1.1.0)"));
    var log = h("pre", "adc-log"); host.appendChild(log);
    host.appendChild(h("p", "adc-foot", "Fixed and Security never appear in the draft: a diff cannot tell a bug fix or a vulnerability fix from any other change. Add those lines by hand."));

    function preset(id) { for (var i = 0; i < S.presets.length; i++) if (S.presets[i].id === id) return S.presets[i]; return S.presets[0]; }

    function load(id) {
      var p = preset(id);
      state.preset = p.id; state.custom = false;
      taO.value = JSON.stringify(p.old, null, 2);
      taN.value = JSON.stringify(p["new"], null, 2);
      render();
    }

    function compute() {
      var p = preset(state.preset), o, n;
      err.textContent = "";
      if (state.custom) {
        try { o = JSON.parse(taO.value); n = JSON.parse(taN.value); }
        catch (e) { err.textContent = "Not valid JSON: " + e.message; return null; }
      } else { o = p.old; n = p["new"]; }
      return run(o, n, { ship: state.ship, date: p.date, consumers: p.consumers ? S.consumers : null });
    }

    function render() {
      var p = preset(state.preset);
      Array.prototype.forEach.call(presetRow.querySelectorAll(".adc-preset"), function (b) { b.classList.toggle("is-on", b.getAttribute("data-id") === p.id && !state.custom); });
      [bH, bM].forEach(function (b) { b.classList.toggle("is-on", b.getAttribute("data-ship") === state.ship); });
      note.textContent = state.custom ? "Your edited documents." : p.note;
      var r = compute();
      if (!r) return;
      state.last = r;
      headline.innerHTML = "";
      var big = h("div", "adc-big");
      big.appendChild(h("b", null, r.required === "none" ? "No change" : r.required.toUpperCase()));
      big.appendChild(h("span", null, r.required === "none" ? " nothing to release" : " bump required by SemVer: " + r.fromVersion + " to " + bumpVersion(r.fromVersion, r.required)));
      headline.appendChild(big);
      var pills = h("div", "adc-pills");
      [["breaking", "breaking"], ["non-breaking", "non-breaking"], ["docs-only", "docs only"]].forEach(function (k) {
        var s = h("span", "adc-pill adc-" + k[0]); s.appendChild(h("b", null, String(r.counts[k[0]]))); s.appendChild(document.createTextNode(" " + k[1])); pills.appendChild(s);
      });
      headline.appendChild(pills);
      if (r.shipped !== r.required) headline.appendChild(h("p", "adc-warn", "Shipped as " + r.version + " (a minor) although " + r.counts.breaking + " changes break callers. Every consumer pinned to ^" + parseVer(r.fromVersion).join(".") + " pulls it in automatically."));
      cons.innerHTML = "";
      if (r.consumers) {
        var c = r.consumers;
        var ch = h("div", "adc-chead");
        ch.appendChild(h("span", "adc-clabel", "Who breaks (constructed consumers, simulated)"));
        var two = h("p", "adc-two");
        var s1 = h("span", "adc-silent" + (c.silent ? " is-bad" : "")); s1.appendChild(h("b", null, c.silent + " of " + c.total)); s1.appendChild(document.createTextNode(" broken without warning"));
        var s2 = h("span", "adc-warned"); s2.appendChild(h("b", null, c.warned + " of " + c.total)); s2.appendChild(document.createTextNode(" warned and must migrate"));
        two.appendChild(s1); two.appendChild(s2); ch.appendChild(two); cons.appendChild(ch);
        var grid = h("div", "adc-cgrid");
        c.list.forEach(function (x) {
          var card = h("div", "adc-card" + (x.broken ? (r.shipped === "major" ? " is-warned" : " is-broken") : ""));
          card.appendChild(h("b", null, x.name));
          card.appendChild(h("span", "adc-cstate", x.broken ? (r.shipped === "major" ? "stays on v" + parseVer(r.fromVersion)[0] + ", migrates on notice" : "breaks on next deploy") : "unaffected"));
          if (x.hits.length) card.appendChild(h("span", "adc-chit", x.hits[0] + (x.hits.length > 1 ? " (+" + (x.hits.length - 1) + " more)" : "")));
          grid.appendChild(card);
        });
        cons.appendChild(grid);
      }
      tableWrap.innerHTML = "";
      var t = h("table", "clean adc-table");
      var th = h("tr"); ["Severity", "Operation", "Change", "Pointer ($refs followed)"].forEach(function (x) { th.appendChild(h("th", null, x)); });
      var thead = h("thead"); thead.appendChild(th); t.appendChild(thead);
      var tb = h("tbody");
      var order = { "breaking": 0, "non-breaking": 1, "docs-only": 2 };
      r.changes.slice().sort(function (a, b) { return (order[a.severity] - order[b.severity]) || cmp(a.ptr, b.ptr) || cmp(a.rule, b.rule); }).forEach(function (x) {
        var tr = h("tr");
        var td = h("td"); td.appendChild(h("span", "adc-sev adc-" + x.severity, x.severity)); tr.appendChild(td);
        tr.appendChild(h("td", "adc-op", x.op)); tr.appendChild(h("td", null, x.detail)); tr.appendChild(h("td", "adc-ptr", x.ptr));
        tb.appendChild(tr);
      });
      t.appendChild(tb); tableWrap.appendChild(t);
      log.textContent = r.changelog;
      host.setAttribute("data-required", r.required);
      host.setAttribute("data-shipped", r.shipped);
    }

    runBtn.addEventListener("click", function () { state.custom = true; render(); });
    load(state.preset);
    return {
      load: load,
      setShip: function (s) { state.ship = s; render(); },
      runCustom: function (o, n) { taO.value = JSON.stringify(o, null, 2); taN.value = JSON.stringify(n, null, 2); state.custom = true; render(); return state.last; },
      state: function () { return state.last; }
    };
  }

  function init() {
    var hosts = document.querySelectorAll(".adc-bench");
    var apis = [];
    Array.prototype.forEach.call(hosts, function (el) { apis.push(mount(el)); });
    root.ADC_BENCH = apis[0] || null;
    root.ADC_BENCHES = apis;
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init); else init();
})(typeof window !== "undefined" ? window : this);
