// Node twin of materials/adc_reference.py: runs the browser engine (assets/adc-live.js) headless.
//   node materials/adc-node.js ladder > node.json    every preset x {honest, minor}
//   node materials/adc-node.js test                  the shared rule unit tests (adc_rule_tests.json)
const fs = require("fs"), path = require("path");
const ROOT = path.join(__dirname, "..");
const ADC = require(path.join(ROOT, "assets/adc-live.js"));
const txt = fs.readFileSync(path.join(ROOT, "assets/adc-sample.js"), "utf8");
const S = JSON.parse(txt.slice(txt.indexOf("window.ADC_SAMPLE = ") + 20, txt.lastIndexOf(";")));
const cmd = process.argv[2] || "ladder";
if (cmd === "ladder") {
  const out = {};
  for (const p of S.presets) for (const ship of ["honest", "minor"])
    out[p.id + "/" + ship] = ADC.run(p.old, p.new, { ship, date: p.date, consumers: p.consumers ? S.consumers : null });
  process.stdout.write(JSON.stringify(out, null, 1));
} else {
  const cases = JSON.parse(fs.readFileSync(path.join(__dirname, "adc_rule_tests.json"), "utf8"));
  let fails = 0;
  for (const c of cases) {
    const got = ADC.diff(c.old, c.new).some(x => x.rule === c.rule);
    if (got !== c.fires) { fails++; console.log("FAIL", c.rule, c.desc); }
  }
  console.log(`${cases.length - fails}/${cases.length} cases pass in node`);
  process.exit(fails ? 1 : 0);
}
