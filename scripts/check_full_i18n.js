"use strict";
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const root = path.resolve(__dirname, "..");
const frontend = path.join(root, "frontend");
const html = fs.readFileSync(path.join(frontend, "index.html"), "utf8");
const app = fs.readFileSync(path.join(frontend, "app.js"), "utf8");
const source = fs.readFileSync(path.join(frontend, "i18n.js"), "utf8");
const sandbox = { window: {} };
vm.runInNewContext(source, sandbox, { filename: "frontend/i18n.js" });
const translations = sandbox.window.EMERALD_I18N;
const languages = ["zh-TW", "en", "th"];
if (!translations) throw new Error("window.EMERALD_I18N was not defined.");
const referenceKeys = Object.keys(translations[languages[0]]).sort();
for (const language of languages) {
  const keys = Object.keys(translations[language] || {}).sort();
  const missing = referenceKeys.filter(key => !keys.includes(key));
  const extra = keys.filter(key => !referenceKeys.includes(key));
  const blank = keys.filter(key => !String(translations[language][key] ?? "").trim());
  if (missing.length || extra.length || blank.length) {
    throw new Error(`${language}: missing=[${missing}], extra=[${extra}], blank=[${blank}]`);
  }
}
const usedKeys = new Set();
for (const match of html.matchAll(/data-i18n(?:-placeholder|-aria-label)?="([^"]+)"/g)) usedKeys.add(match[1]);
for (const match of app.matchAll(/\bt\("([^"]+)"/g)) usedKeys.add(match[1]);
for (const language of languages) {
  const missing = [...usedKeys].filter(key => !(key in translations[language])).sort();
  if (missing.length) throw new Error(`${language} missing used keys: ${missing.join(", ")}`);
}
const forbiddenAttrs = [];
for (const tagMatch of html.matchAll(/<[^>]+>/g)) {
  const tag = tagMatch[0];
  if (/\saria-label="/.test(tag) && !/\sdata-i18n-aria-label="/.test(tag)) forbiddenAttrs.push(tag);
  if (/\splaceholder="/.test(tag) && !/\sdata-i18n-placeholder="/.test(tag)) forbiddenAttrs.push(tag);
}
if (forbiddenAttrs.length) throw new Error(`Unlocalized user-facing attributes: ${forbiddenAttrs.join(" | ")}`);
if (!app.includes('button.textContent = t(key);')) throw new Error("Navigation labels are not translated during rebuild.");
if (!app.includes('button.dataset.i18n = key;')) throw new Error("Dynamic navigation buttons are missing data-i18n keys.");
if (!app.includes('translatedDataSource(item.source)')) throw new Error("Attendance source is not translated.");
console.log(`full i18n check passed: ${referenceKeys.length} keys, ${usedKeys.size} used keys, ${languages.length} languages.`);
