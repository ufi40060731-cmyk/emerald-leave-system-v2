"use strict";

const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const root = path.resolve(__dirname, "..");
const frontend = path.join(root, "frontend");
const html = fs.readFileSync(path.join(frontend, "index.html"), "utf8");
const app = fs.readFileSync(path.join(frontend, "app.js"), "utf8");
const i18nSource = fs.readFileSync(path.join(frontend, "i18n.js"), "utf8");

const sandbox = { window: {} };
vm.runInNewContext(i18nSource, sandbox, { filename: "frontend/i18n.js" });
const translations = sandbox.window.EMERALD_I18N;
const expectedLanguages = ["zh-TW", "en", "th"];

if (!translations || typeof translations !== "object") {
  throw new Error("window.EMERALD_I18N was not defined.");
}

const actualLanguages = Object.keys(translations).sort();
if (actualLanguages.join(",") !== expectedLanguages.slice().sort().join(",")) {
  throw new Error(`Expected languages ${expectedLanguages.join(", ")}; got ${actualLanguages.join(", ")}.`);
}

const usedKeys = new Set();
for (const match of html.matchAll(/data-i18n(?:-placeholder|-aria-label)?="([^"]+)"/g)) {
  usedKeys.add(match[1]);
}
for (const match of app.matchAll(/\bt\("([^"]+)"/g)) {
  usedKeys.add(match[1]);
}
[
  "employee", "manager", "hr", "admin",
  "annual_leave", "sick_leave", "personal_leave",
  "manager_pending", "hr_pending", "approved", "rejected"
].forEach(key => usedKeys.add(key));

for (const language of expectedLanguages) {
  const missing = [...usedKeys].filter(key => !(key in translations[language])).sort();
  if (missing.length) {
    throw new Error(`${language} is missing translation keys: ${missing.join(", ")}`);
  }
}

console.log(`i18n check passed: ${usedKeys.size} used keys across ${expectedLanguages.length} languages.`);
