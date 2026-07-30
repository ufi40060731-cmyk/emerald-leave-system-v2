"use strict";

function resolveApiBaseUrl() {
  const explicit = String(window.EMERALD_CONFIG?.API_BASE_URL || "").replace(/\/+$/, "");
  if (explicit) return explicit;
  const localHosts = new Set(["localhost", "127.0.0.1", "::1"]);
  if (window.EMERALD_CONFIG?.AUTO_CONNECT_LOCALHOST && localHosts.has(location.hostname)) {
    return location.origin;
  }
  return "";
}

const CONFIG = Object.freeze({
  APP_MODE: window.EMERALD_CONFIG?.APP_MODE === "production" ? "production" : "demo",
  API_BASE_URL: resolveApiBaseUrl()
});
const I18N = window.EMERALD_I18N || {};
const SUPPORTED_LANGUAGES = ["zh-TW", "en", "th"];
const STORAGE = {
  language: "emerald_v14_4_lang",
  theme: "emerald_v14_4_theme",
  requests: "emerald_v14_4_requests",
  audits: "emerald_v14_4_audits",
  user: "emerald_v14_4_user",
  token: "emerald_v14_4_api_token",
  chat: "emerald_v15_1_chat",
  rotation: "emerald_v15_2_rotation",
  rotationOverrides: "emerald_v15_2_rotation_overrides",
  onboarding: "emerald_v16_onboarding",
  contentConfig: "emerald_v16_2_content_config",
  sopProgress: "emerald_v16_sop_progress",
  attendanceCorrections: "emerald_v16_attendance_corrections",
  notificationReads: "emerald_v16_1_notification_reads"
};
const LEGACY_STORAGE = {
  language: "emerald_v11_lang",
  theme: "emerald_v11_theme",
  requests: "emerald_v11_requests",
  audits: "emerald_v11_audits",
  user: "emerald_v11_user",
  token: "emerald_api_token"
};
const USERS = {
  E001: { name: "Wang", role: "employee", department: "Production", rotationGroup: "A" },
  E002: { name: "Chen", role: "employee", department: "Administration", rotationGroup: "B" },
  M001: { name: "Manager Lin", role: "manager", department: "Production", rotationGroup: "B" },
  HR001: { name: "HR Huang", role: "hr", department: "Administration", rotationGroup: "NONE" },
  A001: { name: "Administrator", role: "admin", department: "Administration", rotationGroup: "NONE" }
};
const NAV = [
  ["dashboard", "dashboard", ["employee", "manager", "hr", "admin"]],
  ["onboarding", "onboarding", ["employee", "manager", "hr", "admin"]],
  ["sops", "sop_center", ["employee", "manager", "hr", "admin"]],
  ["attendance", "attendance", ["employee", "manager", "hr", "admin"]],
  ["apply", "apply", ["employee", "manager", "hr", "admin"]],
  ["requests", "requests", ["employee", "manager", "hr", "admin"]],
  ["employees", "employees", ["hr", "admin"]],
  ["holidays", "holidays", ["hr", "admin"]],
  ["rotation", "rotation_schedule", ["employee", "manager", "hr", "admin"]],
  ["calendar", "calendar", ["employee", "manager", "hr", "admin"]],
  ["ai", "ask_ai", ["employee", "manager", "hr", "admin"]],
  ["reports", "reports", ["manager", "hr", "admin"]],
  ["excel", "excel", ["hr", "admin"]],
  ["notifications", "notifications", ["employee", "manager", "hr", "admin"]],
  ["audit", "audit", ["hr", "admin"]],
  ["settings", "settings", ["employee", "manager", "hr", "admin"]]

];
const DEFAULT_ONBOARDING_ITEMS = Object.freeze([
  { id: "company", key: "onboarding_item_company" },
  { id: "attendance", key: "onboarding_item_attendance" },
  { id: "rotation", key: "onboarding_item_rotation" },
  { id: "leave", key: "onboarding_item_leave" },
  { id: "safety", key: "onboarding_item_safety" },
  { id: "quality", key: "onboarding_item_quality" },
  { id: "confidentiality", key: "onboarding_item_confidentiality" },
  { id: "contacts", key: "onboarding_item_contacts" }
]);
const POLICY_CARDS = [
  ["policy_attendance_title", "policy_attendance_body"],
  ["policy_rotation_title", "policy_rotation_body"],
  ["policy_leave_title", "policy_leave_body"],
  ["policy_safety_title", "policy_safety_body"],
  ["policy_quality_title", "policy_quality_body"],
  ["policy_confidentiality_title", "policy_confidentiality_body"],
  ["policy_emergency_title", "policy_emergency_body"],
  ["policy_conduct_title", "policy_conduct_body"]
];

const SOP_MODULES = [
  { id: 1, code: "ENT-001", category: "company", titleKey: "sop_company_title", summaryKey: "sop_company_summary", version: "PUBLIC-1", status: "confirmed", required: true, roles: ["all"] },
  { id: 2, code: "SYS-001", category: "company", titleKey: "sop_system_access_title", summaryKey: "sop_system_access_summary", version: "1.0", status: "confirmed", required: true, roles: ["all"] },
  { id: 3, code: "ATT-001", category: "attendance", titleKey: "sop_attendance_title", summaryKey: "sop_attendance_summary", version: "1.0", status: "confirmed", required: true, roles: ["all"] },
  { id: 4, code: "ROT-001", category: "attendance", titleKey: "sop_rotation_title", summaryKey: "sop_rotation_summary", version: "1.0", status: "confirmed", required: true, roles: ["all"] },
  { id: 5, code: "LEV-001", category: "leave", titleKey: "sop_leave_title", summaryKey: "sop_leave_summary", version: "1.0", status: "confirmed", required: true, roles: ["all"] },
  { id: 6, code: "SAF-001", category: "safety", titleKey: "sop_safety_title", summaryKey: "sop_safety_summary", version: "HR-DRAFT", status: "draft", required: true, roles: ["all"] },
  { id: 7, code: "QUA-001", category: "quality", titleKey: "sop_quality_title", summaryKey: "sop_quality_summary", version: "HR-DRAFT", status: "draft", required: true, roles: ["production"] },
  { id: 8, code: "SEC-001", category: "security", titleKey: "sop_confidentiality_title", summaryKey: "sop_confidentiality_summary", version: "HR-DRAFT", status: "draft", required: true, roles: ["all"] },
  { id: 9, code: "EMG-001", category: "emergency", titleKey: "sop_emergency_title", summaryKey: "sop_emergency_summary", version: "HR-DRAFT", status: "draft", required: true, roles: ["all"] },
  { id: 10, code: "CON-001", category: "conduct", titleKey: "sop_conduct_title", summaryKey: "sop_conduct_summary", version: "HR-DRAFT", status: "draft", required: true, roles: ["all"] }
];
const DEFAULT_SOP_QUIZ = Object.freeze([
  { id: "q1", key: "quiz_q1", answer: "yes" },
  { id: "q2", key: "quiz_q2", answer: "yes" },
  { id: "q3", key: "quiz_q3", answer: "no" },
  { id: "q4", key: "quiz_q4", answer: "yes" },
  { id: "q5", key: "quiz_q5", answer: "yes" }
]);
const DEFAULT_QUIZ_PASSING_SCORE = 80;

let backendSops = null; // null = not loaded yet, [] = loaded but empty, [...] = loaded with data

function _sopLocalizedText(item, field) {
  const key = { "zh-TW": "zh", en: "en", th: "th" }[lang] || "zh";
  return item[`${field}_${key}`] || item[`${field}_zh`] || "";
}

async function refreshBackendSops() {
  if (!CONFIG.API_BASE_URL || !apiToken) {
    backendSops = null;
    return;
  }
  try {
    const response = await fetch(apiUrl("/api/sops"), { headers: { Authorization: `Bearer ${apiToken}` } });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const catalog = await response.json();
    const role = current?.role || "employee";
    const department = String(current?.department || "").toLowerCase();
    backendSops = catalog
      .filter(entry => {
        const scope = String(entry.role_scope || "all").toLowerCase().split(",").map(s => s.trim());
        return scope.includes("all") || scope.includes(role) || scope.includes(department);
      })
      .map(entry => ({
        id: entry.id,
        code: entry.code,
        category: entry.category,
        version: entry.version,
        status: entry.status === "published" ? "confirmed" : "draft",
        roles: [entry.role_scope || "all"],
        source: "backend",
        titleText: _sopLocalizedText(entry, "title"),
        summaryText: _sopLocalizedText(entry, "summary"),
      }));
  } catch (error) {
    console.info("Unable to load SOPs from backend; using built-in list.", error);
    backendSops = null;
  }
}
const ATTENDANCE_STATUS_KEYS = {
  normal: "attendance_normal", late: "attendance_late", early_leave: "attendance_early_leave",
  missing_punch: "attendance_missing_punch", absent: "attendance_absent", day_off: "scheduled_day_off"
};

const LEAVE_TYPE_ALIASES = {
  "Annual Leave": "annual_leave",
  "Sick Leave": "sick_leave",
  "Personal Leave": "personal_leave",
  annual_leave: "annual_leave",
  sick_leave: "sick_leave",
  personal_leave: "personal_leave"
};
const AUDIT_ALIASES = {
  work_rule_created: "work_rule_created_action",
  work_rule_updated: "work_rule_updated_action",
  work_rule_deactivated: "work_rule_deactivated_action",
  sop_acknowledged: "sop_acknowledge_action",
  sop_created: "sop_created_action",
  sop_updated: "sop_updated_action",
  sop_deleted: "sop_deleted_action",
  attendance_import: "excel_import_action",
  attendance_correction_requested: "attendance_correction_action",
  attendance_correction_approved: "approve_leave_action",
  attendance_correction_rejected: "reject_leave_action",
  password_changed: "password_changed_action",
  admin_password_reset: "admin_password_reset_action",
  user_activated: "user_activated_action",
  user_deactivated: "user_deactivated_action",
  user_photo_updated: "user_photo_updated_action",
  user_photo_removed: "user_photo_removed_action",
  // Kept for older locally-generated demo audit entries (no backend equivalent).
  Login: "login_action",
  Logout: "logout_action",
  "Submit leave": "submit_leave_action",
  "Approve leave": "approve_leave_action",
  "Reject leave": "reject_leave_action",
  "Excel import demo": "excel_import_action",
  "AI query": "ai_query_action",
  "Holiday sync": "holiday_sync_action",
  "SOP acknowledge": "sop_acknowledge_action",
  "SOP quiz": "sop_quiz_action",
  "Attendance correction": "attendance_correction_action"
};
const HOLIDAY_CACHE_PREFIX = "emerald_th_holidays_";
const HOLIDAY_NOTIFICATION_WINDOW_DAYS = 30;
const HOLIDAY_NOTIFICATION_LIMIT = 5;

const HOLIDAY_TRANSLATIONS = Object.freeze({
  "公曆新年": { "zh-TW": "公曆新年", en: "New Year's Day", th: "วันขึ้นปีใหม่" },
  "特別假期": { "zh-TW": "特別假期", en: "Special holiday", th: "วันหยุดพิเศษ" },
  "萬佛節": { "zh-TW": "萬佛節", en: "Makha Bucha Day", th: "วันมาฆบูชา" },
  "恰克里王朝開國紀念日": { "zh-TW": "恰克里王朝開國紀念日", en: "Chakri Memorial Day", th: "วันจักรี" },
  "宋干節（潑水節）": { "zh-TW": "宋干節（潑水節）", en: "Songkran Festival", th: "วันสงกรานต์" },
  "勞動節": { "zh-TW": "勞動節", en: "National Labour Day", th: "วันแรงงานแห่งชาติ" },
  "泰王登基紀念日": { "zh-TW": "泰王登基紀念日", en: "Coronation Day", th: "วันฉัตรมงคล" },
  "春耕節": { "zh-TW": "春耕節", en: "Royal Ploughing Ceremony Day", th: "วันพืชมงคล" },
  "佛誕節": { "zh-TW": "佛誕節", en: "Visakha Bucha Day", th: "วันวิสาขบูชา" },
  "蘇提達王后誕辰日": { "zh-TW": "蘇提達王后誕辰日", en: "Queen Suthida's Birthday", th: "วันเฉลิมพระชนมพรรษาสมเด็จพระนางเจ้าสุทิดาฯ" },
  "國王瓦吉拉隆功誕辰日": { "zh-TW": "國王瓦吉拉隆功誕辰日", en: "King Vajiralongkorn's Birthday", th: "วันเฉลิมพระชนมพรรษาพระบาทสมเด็จพระเจ้าอยู่หัว" },
  "三寶佛節": { "zh-TW": "三寶佛節", en: "Asarnha Bucha Day", th: "วันอาสาฬหบูชา" },
  "守夏節": { "zh-TW": "守夏節", en: "Buddhist Lent Day", th: "วันเข้าพรรษา" },
  "詩麗吉王太后誕辰日（母親節）": { "zh-TW": "詩麗吉王太后誕辰日（母親節）", en: "Queen Sirikit The Queen Mother's Birthday (Mother's Day)", th: "วันเฉลิมพระชนมพรรษาสมเด็จพระบรมราชชนนีพันปีหลวง (วันแม่แห่งชาติ)" },
  "拉瑪九世國王逝世紀念日": { "zh-TW": "拉瑪九世國王逝世紀念日", en: "King Bhumibol Memorial Day", th: "วันนวมินทรมหาราช" },
  "朱拉隆功大帝紀念日": { "zh-TW": "朱拉隆功大帝紀念日", en: "Chulalongkorn Day", th: "วันปิยมหาราช" },
  "拉瑪九世國王普密蓬·阿杜德誕辰紀念日（父親節）": { "zh-TW": "拉瑪九世國王普密蓬·阿杜德誕辰紀念日（父親節）", en: "King Bhumibol's Birthday Memorial (Father's Day)", th: "วันคล้ายวันพระบรมราชสมภพรัชกาลที่ 9 (วันพ่อแห่งชาติ)" },
  "拉瑪九世誕辰日（父親節）": { "zh-TW": "拉瑪九世誕辰日（父親節）", en: "King Bhumibol's Birthday Memorial (Father's Day)", th: "วันคล้ายวันพระบรมราชสมภพรัชกาลที่ 9 (วันพ่อแห่งชาติ)" },
  "泰國憲法紀念日": { "zh-TW": "泰國憲法紀念日", en: "Constitution Day", th: "วันรัฐธรรมนูญ" },
  "憲法紀念日": { "zh-TW": "泰國憲法紀念日", en: "Constitution Day", th: "วันรัฐธรรมนูญ" },
  "元旦前夕": { "zh-TW": "元旦前夕", en: "New Year's Eve", th: "วันสิ้นปี" }
});

const OFFLINE_HOLIDAYS = {
  2026: [
    ["2026-01-01", "公曆新年"], ["2026-01-02", "特別假期"], ["2026-03-03", "萬佛節"],
    ["2026-04-06", "恰克里王朝開國紀念日"], ["2026-04-13", "宋干節（潑水節）"],
    ["2026-04-14", "宋干節（潑水節）"], ["2026-04-15", "宋干節（潑水節）"],
    ["2026-05-01", "勞動節"], ["2026-05-04", "泰王登基紀念日"], ["2026-05-13", "春耕節"],
    ["2026-05-31", "佛誕節"], ["2026-06-01", "佛誕節（補假）"], ["2026-06-03", "蘇提達王后誕辰日"],
    ["2026-07-28", "國王瓦吉拉隆功誕辰日"], ["2026-07-29", "三寶佛節"], ["2026-07-30", "守夏節"],
    ["2026-08-12", "詩麗吉王太后誕辰日（母親節）"], ["2026-10-13", "拉瑪九世國王逝世紀念日"],
    ["2026-10-16", "特別假期（僅曼谷）"], ["2026-10-23", "朱拉隆功大帝紀念日"],
    ["2026-12-05", "拉瑪九世國王普密蓬·阿杜德誕辰紀念日（父親節）"],
    ["2026-12-07", "拉瑪九世國王普密蓬·阿杜德誕辰紀念日（父親節）（補假）"],
    ["2026-12-10", "泰國憲法紀念日"], ["2026-12-31", "元旦前夕"]
  ].map(([date, name]) => ({
    date,
    name,
    names: buildHolidayNames(name),
    holiday_type: "official",
    company_confirmed: false,
    source: "offline-fallback"
  }))
};

const $ = id => document.getElementById(id);
let lang = readStored(STORAGE.language, LEGACY_STORAGE.language) || "zh-TW";
if (!SUPPORTED_LANGUAGES.includes(lang)) lang = "zh-TW";
let dict = I18N[lang] || I18N["zh-TW"] || I18N.en || {};
let current = null;
let requests = loadRequests();
let audits = loadAudits();
let holidays = [];
let holidayDataMeta = {};
let holidayLoadedFrom = "offline";
let apiToken = sessionStorage.getItem(STORAGE.token) || sessionStorage.getItem(LEGACY_STORAGE.token) || "";
let aiHistory = loadAIHistory();
let rotationSettings = loadRotationSettings();
let rotationOverrides = loadRotationOverrides();
let lastLeaveCalculation = null;
const calendarCursor = new Date();

function readStored(primary, legacy) {
  return localStorage.getItem(primary) ?? localStorage.getItem(legacy);
}

function parseStoredJson(primary, legacy, fallback) {
  for (const key of [primary, legacy]) {
    try {
      const value = localStorage.getItem(key);
      if (value) return JSON.parse(value);
    } catch (error) {
      console.info(`Unable to read ${key}.`, error);
    }
  }
  return fallback;
}

function loadAIHistory() {
  try {
    const value = JSON.parse(sessionStorage.getItem(STORAGE.chat) || "[]");
    if (!Array.isArray(value)) return [];
    return value.filter(item => item && ["user", "assistant"].includes(item.role) && typeof item.content === "string").slice(-20);
  } catch (error) {
    console.info("Unable to load chat history.", error);
    return [];
  }
}

function saveAIHistory() {
  sessionStorage.setItem(STORAGE.chat, JSON.stringify(aiHistory.slice(-20)));
}

function loadRotationSettings() {
  const defaults = {
    name: "A/B Saturday Rotation",
    anchorDate: "2026-01-03",
    firstWorkingGroup: "A",
    cycleWeeks: 2,
    saturdayEnabled: true,
    sundayIsDayOff: true
  };
  const value = parseStoredJson(STORAGE.rotation, STORAGE.rotation, defaults);
  return {
    ...defaults,
    ...(value && typeof value === "object" ? value : {})
  };
}

function loadRotationOverrides() {
  const value = parseStoredJson(STORAGE.rotationOverrides, STORAGE.rotationOverrides, []);
  return Array.isArray(value) ? value.filter(item => item?.date && item?.overrideType) : [];
}

function saveRotationState() {
  localStorage.setItem(STORAGE.rotation, JSON.stringify(rotationSettings));
  localStorage.setItem(STORAGE.rotationOverrides, JSON.stringify(rotationOverrides));
}

function normalizeRotationSettings(value = {}) {
  return {
    name: value.name || "A/B Saturday Rotation",
    anchorDate: value.anchorDate || value.anchor_date || "2026-01-03",
    firstWorkingGroup: value.firstWorkingGroup || value.first_working_group || "A",
    cycleWeeks: Number(value.cycleWeeks || value.cycle_weeks || 2),
    saturdayEnabled: value.saturdayEnabled ?? value.saturday_enabled ?? true,
    sundayIsDayOff: value.sundayIsDayOff ?? value.sunday_is_day_off ?? true
  };
}

function normalizeOverride(value = {}) {
  return {
    id: value.id || Date.now(),
    date: String(value.date || "").slice(0, 10),
    overrideType: value.overrideType || value.override_type || "DAY_OFF",
    rotationGroup: value.rotationGroup || value.rotation_group || "ALL",
    note: value.note || ""
  };
}

function loadRequests() {
  const defaults = [
    { id: 1001, user: "E001 Wang", type: "annual_leave", date: "2026-07-20 ~ 2026-07-21", status: "manager_pending" },
    { id: 1002, user: "E002 Chen", type: "sick_leave", date: "2026-07-15", status: "hr_pending" },
    { id: 1003, user: "M001 Manager Lin", type: "annual_leave", date: "2026-07-05", status: "approved" }
  ];
  const stored = parseStoredJson(STORAGE.requests, LEGACY_STORAGE.requests, defaults);
  if (!Array.isArray(stored)) return defaults;
  return stored.map(item => ({
    ...item,
    type: LEAVE_TYPE_ALIASES[item.type] || item.type || "annual_leave",
    workdays: Number(item.workdays || 0)
  }));
}

function loadAudits() {
  const stored = parseStoredJson(STORAGE.audits, LEGACY_STORAGE.audits, []);
  if (!Array.isArray(stored)) return [];
  return stored.map(item => ({
    ...item,
    action: AUDIT_ALIASES[item.action] || item.action
  }));
}

function interpolate(template, values = {}) {
  return String(template).replace(/\{(\w+)\}/g, (_, key) => values[key] ?? "");
}

function t(key, values = {}) {
  const value = dict[key] ?? I18N.en?.[key] ?? key;
  return interpolate(value, values);
}

function apiUrl(path) {
  return CONFIG.API_BASE_URL ? `${CONFIG.API_BASE_URL}${path}` : "";
}

async function readJsonSafely(response) {
  try {
    return await response.json();
  } catch {
    return {};
  }
}

function localIsoDate(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function parseIsoDate(value) {
  const [year, month, day] = String(value || "").split("-").map(Number);
  if (!year || !month || !day) return null;
  const result = new Date(year, month - 1, day);
  return Number.isNaN(result.getTime()) ? null : result;
}

function currentRotationGroup() {
  return String(current?.rotationGroup || current?.rotation_group || "NONE").toUpperCase();
}

function saturdayWorkingGroup(date) {
  if (!rotationSettings.saturdayEnabled || date.getDay() !== 6) return null;
  const anchor = parseIsoDate(rotationSettings.anchorDate);
  if (!anchor) return null;
  const weeks = Math.floor((date.getTime() - anchor.getTime()) / 604800000);
  const first = rotationSettings.firstWorkingGroup === "B" ? "B" : "A";
  return Math.abs(weeks % 2) === 0 ? first : (first === "A" ? "B" : "A");
}

function matchingRotationOverride(dateText, group) {
  const matches = rotationOverrides.filter(item => item.date === dateText);
  return matches.find(item => item.rotationGroup === group) || matches.find(item => item.rotationGroup === "ALL") || null;
}

function classifyDemoDate(date, group = currentRotationGroup()) {
  const key = localIsoDate(date);
  const override = matchingRotationOverride(key, group);
  if (override) {
    const workday = override.overrideType === "WORKDAY";
    return { date: key, isWorkday: workday, category: workday ? "override_workday" : "override_day_off", workingGroup: saturdayWorkingGroup(date), note: override.note };
  }
  if (holidays.some(item => holidayDate(item) === key)) {
    return { date: key, isWorkday: false, category: "holiday", workingGroup: saturdayWorkingGroup(date), note: "" };
  }
  if (date.getDay() === 0 && rotationSettings.sundayIsDayOff) {
    return { date: key, isWorkday: false, category: "sunday", workingGroup: null, note: "" };
  }
  if (date.getDay() === 6) {
    if (!rotationSettings.saturdayEnabled) return { date: key, isWorkday: false, category: "saturday_day_off", workingGroup: null, note: "" };
    const workingGroup = saturdayWorkingGroup(date);
    const isWorkday = ["A", "B"].includes(group) && group === workingGroup;
    return { date: key, isWorkday, category: isWorkday ? "rotation_workday" : "rotation_day_off", workingGroup, note: "" };
  }
  return { date: key, isWorkday: true, category: "weekday", workingGroup: null, note: "" };
}

function calculateDemoLeave(startText, endText) {
  const start = parseIsoDate(startText);
  const end = parseIsoDate(endText);
  if (!start || !end || end < start) return null;
  const details = [];
  const cursor = new Date(start);
  while (cursor <= end) {
    details.push(classifyDemoDate(cursor));
    cursor.setDate(cursor.getDate() + 1);
  }
  const count = category => details.filter(item => item.category === category).length;
  return {
    start_date: startText, end_date: endText, rotation_group: currentRotationGroup(),
    calendar_days: details.length, workdays: details.filter(item => item.isWorkday).length,
    holidays: count("holiday"), sundays: count("sunday"),
    rotation_days_off: count("rotation_day_off"), rotation_workdays: count("rotation_workday"),
    override_days_off: count("override_day_off"), override_workdays: count("override_workday"),
    details
  };
}



function cloneManagedDefaults() {
  return {
    onboardingItems: DEFAULT_ONBOARDING_ITEMS.map(item => ({ ...item, texts: {} })),
    quizQuestions: DEFAULT_SOP_QUIZ.map(item => ({ ...item, texts: {} })),
    passingScore: DEFAULT_QUIZ_PASSING_SCORE,
    quizVersion: 1
  };
}

function normalizeManagedId(value, prefix, index) {
  const normalized = String(value || "")
    .toLowerCase()
    .replace(/[^a-z0-9_-]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 48);
  return normalized || `${prefix}-${index + 1}`;
}

function normalizeManagedTexts(value) {
  const result = {};
  const source = value && typeof value === "object" ? value : {};
  SUPPORTED_LANGUAGES.forEach(code => {
    const text = String(source[code] || "").trim();
    if (text) result[code] = text.slice(0, 500);
  });
  return result;
}

function loadContentConfig() {
  const defaults = cloneManagedDefaults();
  try {
    const parsed = JSON.parse(localStorage.getItem(STORAGE.contentConfig) || "null");
    if (!parsed || typeof parsed !== "object") return defaults;
    const usedOnboardingIds = new Set();
    const onboardingItems = (Array.isArray(parsed.onboardingItems) ? parsed.onboardingItems : defaults.onboardingItems)
      .map((item, index) => {
        let id = normalizeManagedId(item?.id, "item", index);
        while (usedOnboardingIds.has(id)) id = `${id}-${index + 1}`;
        usedOnboardingIds.add(id);
        return {
          id,
          key: typeof item?.key === "string" ? item.key : "",
          texts: normalizeManagedTexts(item?.texts || (item?.text ? { "zh-TW": item.text } : {}))
        };
      })
      .filter(item => item.key || Object.keys(item.texts).length);

    const usedQuizIds = new Set();
    const quizQuestions = (Array.isArray(parsed.quizQuestions) ? parsed.quizQuestions : defaults.quizQuestions)
      .map((item, index) => {
        let id = normalizeManagedId(item?.id, "question", index);
        while (usedQuizIds.has(id)) id = `${id}-${index + 1}`;
        usedQuizIds.add(id);
        return {
          id,
          key: typeof item?.key === "string" ? item.key : "",
          texts: normalizeManagedTexts(item?.texts || (item?.text ? { "zh-TW": item.text } : {})),
          answer: item?.answer === "no" ? "no" : "yes"
        };
      })
      .filter(item => item.key || Object.keys(item.texts).length);

    return {
      onboardingItems: onboardingItems.length ? onboardingItems : defaults.onboardingItems,
      quizQuestions: quizQuestions.length ? quizQuestions : defaults.quizQuestions,
      passingScore: Math.min(100, Math.max(60, Number(parsed.passingScore || DEFAULT_QUIZ_PASSING_SCORE))),
      quizVersion: Math.max(1, Number(parsed.quizVersion || 1))
    };
  } catch (error) {
    console.info("Unable to load managed onboarding content.", error);
    return defaults;
  }
}

function saveContentConfig(config) {
  localStorage.setItem(STORAGE.contentConfig, JSON.stringify(config));
}

function managedText(item) {
  const texts = item?.texts && typeof item.texts === "object" ? item.texts : {};
  if (String(texts[lang] || "").trim()) return String(texts[lang]).trim();
  if (item?.key) {
    const translated = I18N[lang]?.[item.key];
    if (translated) return String(translated);
  }
  return t("translation_missing_text");
}

function managedEditorTexts(item) {
  const texts = normalizeManagedTexts(item?.texts);
  if (item?.key) {
    SUPPORTED_LANGUAGES.forEach(code => {
      if (!texts[code] && I18N[code]?.[item.key]) texts[code] = String(I18N[code][item.key]);
    });
  }
  return texts;
}

const MANAGED_FIELD_SUFFIX = Object.freeze({ "zh-TW": "Zh", en: "En", th: "Th" });
const MANAGED_LANGUAGE_LABEL_KEYS = Object.freeze({ "zh-TW": "translation_zh_tw", en: "translation_en", th: "translation_th" });

function managedFieldId(prefix, code) {
  return `${prefix}${MANAGED_FIELD_SUFFIX[code]}`;
}

function readManagedTranslationFields(prefix) {
  const texts = {};
  SUPPORTED_LANGUAGES.forEach(code => {
    const value = String($(managedFieldId(prefix, code))?.value || "").trim();
    if (value) texts[code] = value.slice(0, 500);
  });
  return texts;
}

function fillManagedTranslationFields(prefix, item) {
  const texts = managedEditorTexts(item);
  SUPPORTED_LANGUAGES.forEach(code => {
    const element = $(managedFieldId(prefix, code));
    if (element) element.value = texts[code] || "";
  });
}

function clearManagedTranslationFields(prefix) {
  SUPPORTED_LANGUAGES.forEach(code => {
    const element = $(managedFieldId(prefix, code));
    if (element) element.value = "";
  });
}

function missingManagedLanguages(itemOrTexts) {
  const texts = itemOrTexts?.key ? managedEditorTexts(itemOrTexts) : normalizeManagedTexts(itemOrTexts);
  return SUPPORTED_LANGUAGES.filter(code => !String(texts[code] || "").trim());
}

function managedTranslationStatus(item) {
  const missing = missingManagedLanguages(item);
  if (!missing.length) return t("translation_complete");
  const languages = missing.map(code => t(MANAGED_LANGUAGE_LABEL_KEYS[code])).join(" / ");
  return t("translation_incomplete", { languages });
}

function translatedDataSource(value) {
  const normalized = String(value || "").trim().toLowerCase();
  const key = `source_${normalized}`;
  return normalized && I18N[lang]?.[key] ? t(key) : (String(value || "").trim() || "—");
}

function nextManagedId(prefix) {
  return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`;
}

function canManageOnboardingContent() {
  return Boolean(current && ["hr", "admin"].includes(current.role));
}

function bumpQuizVersion(config) {
  config.quizVersion = Math.max(Date.now(), Number(config.quizVersion || 1) + 1);
}

function setContentManagerMessage(id, message, isError = false) {
  const element = $(id);
  if (!element) return;
  element.textContent = message || "";
  element.classList.toggle("manager-error", Boolean(isError));
}

function toggleManagerPanel(panelId, buttonId) {
  if (!canManageOnboardingContent()) return;
  const panel = $(panelId);
  const button = $(buttonId);
  if (!panel || !button) return;
  panel.classList.toggle("hidden");
  button.textContent = panel.classList.contains("hidden") ? t("content_manage") : t("content_close");
}

function renderOnboardingManager(config = loadContentConfig()) {
  const button = $("toggleOnboardingManager");
  const panel = $("onboardingManager");
  const list = $("onboardingManagerList");
  const canManage = canManageOnboardingContent();
  if (button) {
    button.hidden = !canManage;
    button.textContent = panel?.classList.contains("hidden") ? t("content_manage") : t("content_close");
  }
  if (!panel || !list) return;
  if (!canManage) {
    panel.classList.add("hidden");
    return;
  }
  list.innerHTML = config.onboardingItems.map((item, index) =>
    `<div class="manager-row"><span class="manager-index">${index + 1}</span>` +
    `<span class="manager-text">${escapeHtml(managedText(item))}<small>${escapeHtml(managedTranslationStatus(item))}</small></span>` +
    `<div class="manager-actions"><button type="button" class="soft" data-onboarding-edit="${escapeHtml(item.id)}">${escapeHtml(t("content_edit"))}</button>` +
    `<button type="button" class="ghost danger" data-onboarding-delete="${escapeHtml(item.id)}">${escapeHtml(t("content_delete"))}</button></div></div>`
  ).join("");
  list.querySelectorAll("[data-onboarding-edit]").forEach(buttonElement => {
    buttonElement.onclick = () => {
      const item = config.onboardingItems.find(entry => entry.id === buttonElement.dataset.onboardingEdit);
      if (!item) return;
      $("onboardingEditId").value = item.id;
      fillManagedTranslationFields("onboardingItemText", item);
      $("onboardingItemTextZh")?.focus();
      setContentManagerMessage("onboardingManagerMessage", "");
    };
  });
  list.querySelectorAll("[data-onboarding-delete]").forEach(buttonElement => {
    buttonElement.onclick = () => deleteOnboardingContentItem(buttonElement.dataset.onboardingDelete);
  });
}

function clearOnboardingEditor() {
  if ($("onboardingEditId")) $("onboardingEditId").value = "";
  clearManagedTranslationFields("onboardingItemText");
}

function saveOnboardingContentItem() {
  if (!canManageOnboardingContent()) return;
  const texts = readManagedTranslationFields("onboardingItemText");
  if (missingManagedLanguages(texts).length) {
    setContentManagerMessage("onboardingManagerMessage", t("content_all_languages_required"), true);
    return;
  }
  const editId = String($("onboardingEditId")?.value || "");
  const config = loadContentConfig();
  if (editId) {
    const item = config.onboardingItems.find(entry => entry.id === editId);
    if (!item) return;
    item.texts = texts;
  } else {
    config.onboardingItems.push({ id: nextManagedId("item"), key: "", texts });
  }
  saveContentConfig(config);
  clearOnboardingEditor();
  setContentManagerMessage("onboardingManagerMessage", t("content_saved"));
  renderOnboarding();
}

function deleteOnboardingContentItem(id) {
  if (!canManageOnboardingContent()) return;
  const config = loadContentConfig();
  if (config.onboardingItems.length <= 1) {
    setContentManagerMessage("onboardingManagerMessage", t("content_minimum_one"), true);
    return;
  }
  if (!window.confirm(t("content_confirm_delete"))) return;
  config.onboardingItems = config.onboardingItems.filter(item => item.id !== id);
  saveContentConfig(config);
  clearOnboardingEditor();
  renderOnboarding();
  setContentManagerMessage("onboardingManagerMessage", t("content_deleted"));
}

function restoreDefaultOnboardingContent() {
  if (!canManageOnboardingContent() || !window.confirm(t("content_confirm_reset"))) return;
  const config = loadContentConfig();
  config.onboardingItems = cloneManagedDefaults().onboardingItems;
  saveContentConfig(config);
  clearOnboardingEditor();
  renderOnboarding();
  setContentManagerMessage("onboardingManagerMessage", t("content_saved"));
}

function renderSopQuiz() {
  const container = $("sopQuizQuestions");
  if (!container) return;
  const config = loadContentConfig();
  const progress = loadSopProgress();
  if ($("sopQuizIntro")) $("sopQuizIntro").textContent = t("sop_quiz_intro_dynamic", { count: config.quizQuestions.length, score: config.passingScore });
  container.innerHTML = config.quizQuestions.map((question, index) =>
    `<div class="quiz-question"><p><b>${index + 1}.</b> ${escapeHtml(managedText(question))}</p>` +
    `<div class="quiz-options"><label><input type="radio" name="sopQuiz_${escapeHtml(question.id)}" value="yes"> <span>${escapeHtml(t("quiz_yes"))}</span></label>` +
    `<label><input type="radio" name="sopQuiz_${escapeHtml(question.id)}" value="no"> <span>${escapeHtml(t("quiz_no"))}</span></label></div></div>`
  ).join("");
  if ($("sopQuizScore")) $("sopQuizScore").textContent = progress.quizScore ? t("sop_quiz_score", { score: progress.quizScore }) : "";
  renderQuizManager(config);
}

function renderQuizManager(config = loadContentConfig()) {
  const button = $("toggleQuizManager");
  const panel = $("quizManager");
  const list = $("quizManagerList");
  const canManage = canManageOnboardingContent();
  if (button) {
    button.hidden = !canManage;
    button.textContent = panel?.classList.contains("hidden") ? t("content_manage") : t("content_close");
  }
  if (!panel || !list) return;
  if (!canManage) {
    panel.classList.add("hidden");
    return;
  }
  if ($("quizPassingScore")) $("quizPassingScore").value = String(config.passingScore);
  list.innerHTML = config.quizQuestions.map((question, index) =>
    `<div class="manager-row"><span class="manager-index">${index + 1}</span>` +
    `<span class="manager-text">${escapeHtml(managedText(question))}<small>${escapeHtml(t("quiz_correct_answer"))}: ${escapeHtml(t(question.answer === "yes" ? "quiz_yes" : "quiz_no"))} · ${escapeHtml(managedTranslationStatus(question))}</small></span>` +
    `<div class="manager-actions"><button type="button" class="soft" data-quiz-edit="${escapeHtml(question.id)}">${escapeHtml(t("content_edit"))}</button>` +
    `<button type="button" class="ghost danger" data-quiz-delete="${escapeHtml(question.id)}">${escapeHtml(t("content_delete"))}</button></div></div>`
  ).join("");
  list.querySelectorAll("[data-quiz-edit]").forEach(buttonElement => {
    buttonElement.onclick = () => {
      const question = config.quizQuestions.find(entry => entry.id === buttonElement.dataset.quizEdit);
      if (!question) return;
      $("quizEditId").value = question.id;
      fillManagedTranslationFields("quizQuestionText", question);
      $("quizCorrectAnswer").value = question.answer;
      $("quizQuestionTextZh")?.focus();
      setContentManagerMessage("quizManagerMessage", "");
    };
  });
  list.querySelectorAll("[data-quiz-delete]").forEach(buttonElement => {
    buttonElement.onclick = () => deleteQuizQuestion(buttonElement.dataset.quizDelete);
  });
}

function clearQuizEditor() {
  if ($("quizEditId")) $("quizEditId").value = "";
  clearManagedTranslationFields("quizQuestionText");
  if ($("quizCorrectAnswer")) $("quizCorrectAnswer").value = "yes";
}

function saveQuizQuestion() {
  if (!canManageOnboardingContent()) return;
  const texts = readManagedTranslationFields("quizQuestionText");
  if (missingManagedLanguages(texts).length) {
    setContentManagerMessage("quizManagerMessage", t("content_all_languages_required"), true);
    return;
  }
  const answer = $("quizCorrectAnswer")?.value === "no" ? "no" : "yes";
  const editId = String($("quizEditId")?.value || "");
  const config = loadContentConfig();
  if (editId) {
    const question = config.quizQuestions.find(entry => entry.id === editId);
    if (!question) return;
    question.texts = texts;
    question.answer = answer;
  } else {
    config.quizQuestions.push({ id: nextManagedId("question"), key: "", texts, answer });
  }
  bumpQuizVersion(config);
  saveContentConfig(config);
  clearQuizEditor();
  renderSopQuiz();
  renderSops();
  setContentManagerMessage("quizManagerMessage", t("quiz_changed_reset"));
}

function deleteQuizQuestion(id) {
  if (!canManageOnboardingContent()) return;
  const config = loadContentConfig();
  if (config.quizQuestions.length <= 1) {
    setContentManagerMessage("quizManagerMessage", t("content_minimum_one"), true);
    return;
  }
  if (!window.confirm(t("content_confirm_delete"))) return;
  config.quizQuestions = config.quizQuestions.filter(question => question.id !== id);
  bumpQuizVersion(config);
  saveContentConfig(config);
  clearQuizEditor();
  renderSopQuiz();
  renderSops();
  setContentManagerMessage("quizManagerMessage", t("quiz_changed_reset"));
}

function saveQuizPassingScore() {
  if (!canManageOnboardingContent()) return;
  const value = Number($("quizPassingScore")?.value || DEFAULT_QUIZ_PASSING_SCORE);
  if (!Number.isFinite(value) || value < 60 || value > 100) {
    setContentManagerMessage("quizManagerMessage", t("quiz_score_range"), true);
    return;
  }
  const config = loadContentConfig();
  config.passingScore = Math.round(value);
  bumpQuizVersion(config);
  saveContentConfig(config);
  renderSopQuiz();
  renderSops();
  setContentManagerMessage("quizManagerMessage", t("quiz_changed_reset"));
}

function restoreDefaultQuizContent() {
  if (!canManageOnboardingContent() || !window.confirm(t("content_confirm_reset"))) return;
  const config = loadContentConfig();
  const defaults = cloneManagedDefaults();
  config.quizQuestions = defaults.quizQuestions;
  config.passingScore = defaults.passingScore;
  bumpQuizVersion(config);
  saveContentConfig(config);
  clearQuizEditor();
  renderSopQuiz();
  renderSops();
  setContentManagerMessage("quizManagerMessage", t("quiz_changed_reset"));
}


function sopProgressKey() {
  return `${STORAGE.sopProgress}_${current?.id || "guest"}`;
}

function loadSopProgress() {
  try {
    const value = JSON.parse(localStorage.getItem(sopProgressKey()) || "{}");
    const config = loadContentConfig();
    const storedVersion = Number(value.quizVersion || 1);
    const quizCurrent = storedVersion === Number(config.quizVersion || 1);
    return {
      acknowledged: value.acknowledged || {},
      quizScore: quizCurrent ? Number(value.quizScore || 0) : 0,
      quizPassed: quizCurrent && Boolean(value.quizPassed),
      quizVersion: storedVersion
    };
  } catch (error) {
    console.info("Unable to load SOP progress.", error);
    return { acknowledged: {}, quizScore: 0, quizPassed: false, quizVersion: 1 };
  }
}

function saveSopProgress(value) {
  localStorage.setItem(sopProgressKey(), JSON.stringify(value));
}

function applicableSops() {
  const role = current?.role || "employee";
  const department = String(current?.department || "").toLowerCase();
  if (Array.isArray(backendSops) && backendSops.length > 0) return backendSops;
  return SOP_MODULES.filter(item => item.roles.includes("all") || item.roles.includes(role) || item.roles.includes(department));
}

function renderEnterpriseKpis() {
  const progress = loadSopProgress();
  const modules = applicableSops().filter(item => item.status === "confirmed");
  const completed = modules.filter(item => progress.acknowledged[item.code]).length;
  const percent = modules.length ? Math.round(completed / modules.length * 100) : 0;
  if ($("enterpriseSopPercent")) $("enterpriseSopPercent").textContent = `${percent}%`;
  if ($("enterpriseSopPending")) $("enterpriseSopPending").textContent = String(Math.max(modules.length - completed, 0));
  if ($("enterpriseAttendanceRate")) {
    if (CONFIG.API_BASE_URL && apiToken) {
      fetch(apiUrl("/api/attendance/summary"), { headers: { Authorization: `Bearer ${apiToken}` } })
        .then(response => response.ok ? response.json() : null)
        .then(summary => {
          if (summary && $("enterpriseAttendanceRate")) {
            $("enterpriseAttendanceRate").textContent = `${summary.normal_rate}%`;
          }
        })
        .catch(error => console.info("Attendance summary unavailable.", error));
    } else {
      $("enterpriseAttendanceRate").textContent = "96%";
    }
  }
}

function renderSops() {
  const grid = $("sopGrid");
  if (!grid) return;
  const progress = loadSopProgress();
  const query = String($("sopSearch")?.value || "").trim().toLowerCase();
  const category = $("sopCategory")?.value || "all";
  const sopTitle = item => item.source === "backend" ? item.titleText : t(item.titleKey);
  const sopSummary = item => item.source === "backend" ? item.summaryText : t(item.summaryKey);
  const modules = applicableSops().filter(item => {
    const text = `${sopTitle(item)} ${sopSummary(item)} ${item.code}`.toLowerCase();
    return (category === "all" || item.category === category) && (!query || text.includes(query));
  });
  grid.innerHTML = modules.length ? modules.map(item => {
    const acknowledged = Boolean(progress.acknowledged[item.code]);
    const confirmed = item.status === "confirmed";
    const statusClass = confirmed ? "approved" : "pending";
    const statusText = confirmed ? t("sop_confirmed") : t("sop_draft");
    const actionText = acknowledged ? t("sop_acknowledged") : t("sop_acknowledge");
    return `<article class="sop-card ${acknowledged ? "completed" : ""}">` +
      `<div class="sop-card-head"><span class="badge ${statusClass}">${escapeHtml(statusText)}</span><code>${escapeHtml(item.code)}</code></div>` +
      `<h4>${escapeHtml(sopTitle(item))}</h4><p>${escapeHtml(sopSummary(item))}</p>` +
      `<div class="sop-meta"><span>${escapeHtml(t("sop_version"))}: ${escapeHtml(item.version)}</span><span>${escapeHtml(t(`category_${item.category}`) || item.category)}</span></div>` +
      `<div class="sop-actions"><button type="button" class="soft" data-sop-ai="${escapeHtml(sopTitle(item))}">${escapeHtml(t("sop_ask_ai"))}</button>` +
      `<button type="button" class="${acknowledged ? "ghost" : "primary"}" data-sop-ack="${escapeHtml(item.code)}" ${!confirmed || acknowledged ? "disabled" : ""}>${escapeHtml(actionText)}</button></div>` +
      `${!confirmed ? `<small>${escapeHtml(t("hr_confirmed_only"))}</small>` : ""}</article>`;
  }).join("") : `<div class="empty-state">${escapeHtml(t("sop_no_results"))}</div>`;

  grid.querySelectorAll("[data-sop-ai]").forEach(button => {
    button.onclick = () => openOnboardingAI(button.dataset.sopAi);
  });
  grid.querySelectorAll("[data-sop-ack]").forEach(button => {
    button.onclick = async () => {
      const code = button.dataset.sopAck;
      const item = applicableSops().find(entry => entry.code === code);
      if (!item) return;
      if (!progress.quizPassed) {
        $("sopQuizMessage").textContent = t("sop_quiz_required", { score: loadContentConfig().passingScore });
        $("sopQuiz").scrollIntoView({ behavior: "smooth", block: "center" });
        return;
      }
      if (CONFIG.API_BASE_URL && apiToken) {
        try {
          let backendSopId = item.id;
          if (item.source !== "backend") {
            const catalogResponse = await fetch(apiUrl("/api/sops"), { headers: { Authorization: `Bearer ${apiToken}` } });
            if (catalogResponse.ok) {
              const catalog = await catalogResponse.json();
              backendSopId = catalog.find(entry => entry.code === item.code)?.id || backendSopId;
            }
          }
          const response = await fetch(apiUrl(`/api/sops/${backendSopId}/acknowledge`), {
            method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${apiToken}` },
            body: JSON.stringify({ quiz_score: progress.quizScore, passing_score: loadContentConfig().passingScore })
          });
          if (!response.ok) throw new Error(`HTTP ${response.status}`);
        } catch (error) {
          console.info("Backend SOP acknowledgement unavailable; storing locally.", error);
        }
      }
      const next = loadSopProgress();
      next.acknowledged[code] = { version: item.version, at: new Date().toISOString() };
      saveSopProgress(next);
      addAudit("sop_acknowledge_action");
      renderSops();
      renderEnterpriseKpis();
    };
  });
  const required = applicableSops().filter(item => item.status === "confirmed");
  const done = required.filter(item => progress.acknowledged[item.code]).length;
  const percent = required.length ? Math.round(done / required.length * 100) : 0;
  if ($("sopProgressText")) $("sopProgressText").textContent = t("sop_progress", { done, total: required.length });
  if ($("sopProgressBar")) $("sopProgressBar").style.width = `${percent}%`;
  if ($("sopQuizScore")) $("sopQuizScore").textContent = progress.quizScore ? t("sop_quiz_score", { score: progress.quizScore }) : "";
}

function submitSopQuiz() {
  const config = loadContentConfig();
  let correct = 0;
  let answered = 0;
  config.quizQuestions.forEach(question => {
    const selected = document.querySelector(`input[name="sopQuiz_${question.id}"]:checked`);
    if (selected) {
      answered += 1;
      if (selected.value === question.answer) correct += 1;
    }
  });
  const score = config.quizQuestions.length ? Math.round(correct / config.quizQuestions.length * 100) : 0;
  const progress = loadSopProgress();
  progress.quizScore = score;
  progress.quizPassed = answered === config.quizQuestions.length && score >= config.passingScore;
  progress.quizVersion = config.quizVersion;
  saveSopProgress(progress);
  $("sopQuizMessage").textContent = progress.quizPassed
    ? t("sop_quiz_pass", { score })
    : t("sop_quiz_fail", { score, required: config.passingScore });
  addAudit("sop_quiz_action");
  renderSops();
  renderSopQuiz();
}

function buildDemoAttendance() {
  const items = [];
  const today = new Date();
  const cursor = new Date(today.getFullYear(), today.getMonth(), 1);
  const patterns = [
    ["07:54", "17:05", "normal"], ["08:11", "17:02", "late"], ["07:58", "16:31", "early_leave"],
    ["—", "17:08", "missing_punch"], ["07:52", "17:16", "normal"], ["07:57", "17:01", "normal"]
  ];
  let index = 0;
  while (cursor <= today && items.length < 14) {
    const result = classifyDemoDate(cursor);
    if (result.isWorkday) {
      const pattern = patterns[index % patterns.length];
      items.push({
        id: index + 1, employee_id: current?.id || "E001", work_date: localIsoDate(cursor),
        scheduled_start: "08:00", scheduled_end: "17:00", clock_in: pattern[0], clock_out: pattern[1],
        status: pattern[2], source: "demo", note: ""
      });
      index += 1;
    }
    cursor.setDate(cursor.getDate() + 1);
  }
  return items.reverse();
}

async function loadAttendanceRecords() {
  if (CONFIG.API_BASE_URL && apiToken) {
    try {
      const response = await fetch(apiUrl("/api/attendance"), { headers: { Authorization: `Bearer ${apiToken}` } });
      if (response.ok) return await response.json();
    } catch (error) {
      console.info("Attendance API unavailable; using demo data.", error);
    }
  }
  return buildDemoAttendance();
}

async function renderAttendance() {
  const rows = $("attendanceRows");
  if (!rows || !current) return;
  const items = await loadAttendanceRecords();
  rows.innerHTML = items.length ? items.map(item => `<tr>` +
    `<td>${escapeHtml(item.work_date)}</td><td>${escapeHtml(item.scheduled_start || "—")}–${escapeHtml(item.scheduled_end || "—")}</td>` +
    `<td>${escapeHtml(item.clock_in || "—")}</td><td>${escapeHtml(item.clock_out || "—")}</td>` +
    `<td><span class="badge ${item.status === "normal" ? "approved" : item.status === "absent" ? "rejected" : "pending"}">${escapeHtml(t(ATTENDANCE_STATUS_KEYS[item.status] || "no_data"))}</span></td>` +
    `<td>${escapeHtml(translatedDataSource(item.source))}</td></tr>`).join("") : `<tr><td colspan="6">${escapeHtml(t("no_data"))}</td></tr>`;
  const normal = items.filter(item => item.status === "normal").length;
  const late = items.filter(item => item.status === "late").length;
  const missing = items.filter(item => item.status === "missing_punch").length;
  const rate = items.length ? Math.round(normal / items.length * 100) : 100;
  $("attendanceRate").textContent = `${rate}%`;
  $("attendanceLateCount").textContent = String(late);
  $("attendanceMissingCount").textContent = String(missing);
  $("attendanceOvertime").textContent = "4.5";
  window.__emeraldAttendance = items;
  renderEnterpriseKpis();
  if (["manager", "hr", "admin"].includes(current.role)) {
    renderCorrectionReview();
  } else if ($("correctionReviewCard")) {
    $("correctionReviewCard").classList.add("hidden");
  }
}

async function renderCorrectionReview() {
  const card = $("correctionReviewCard");
  const rows = $("correctionReviewRows");
  if (!card || !rows) return;
  card.classList.remove("hidden");

  if (!CONFIG.API_BASE_URL || !apiToken) {
    rows.innerHTML = `<tr><td colspan="7">${escapeHtml(t("backend_unavailable"))}</td></tr>`;
    return;
  }

  try {
    const response = await fetch(apiUrl("/api/attendance/corrections"), {
      headers: { Authorization: `Bearer ${apiToken}` }
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const items = await response.json();
    window.__emeraldCorrections = items;

    rows.innerHTML = items.length ? items.map(item => {
      const employeeName = USERS[item.employee_id]?.name;
      const employeeLabel = employeeName ? `${item.employee_id} ${employeeName}` : item.employee_id;
      const statusClass = item.status === "approved" ? "approved" : item.status === "rejected" ? "rejected" : "pending";
      const actions = item.status === "pending"
        ? `<button class="soft" onclick="reviewCorrection(${item.id},'approved')">${escapeHtml(t("approve"))}</button>` +
          `<button class="ghost" onclick="reviewCorrection(${item.id},'rejected')">${escapeHtml(t("reject"))}</button>`
        : "";
      return `<tr>` +
        `<td>${escapeHtml(employeeLabel)}</td>` +
        `<td>${escapeHtml(item.requested_clock_in ? item.requested_clock_in.slice(0, 10) : "—")}</td>` +
        `<td>${escapeHtml(item.requested_clock_in || "—")}</td>` +
        `<td>${escapeHtml(item.requested_clock_out || "—")}</td>` +
        `<td>${escapeHtml(item.reason)}</td>` +
        `<td><span class="badge ${statusClass}">${escapeHtml(t(item.status) || item.status)}</span></td>` +
        `<td><div class="row-actions">${actions}</div></td>` +
        `</tr>`;
    }).join("") : `<tr><td colspan="7">${escapeHtml(t("no_data"))}</td></tr>`;
  } catch (error) {
    console.info("Could not load attendance corrections.", error);
    rows.innerHTML = `<tr><td colspan="7">${escapeHtml(t("backend_unavailable"))}</td></tr>`;
  }
}

window.reviewCorrection = async (correctionId, status) => {
  if (!CONFIG.API_BASE_URL || !apiToken) return;
  const note = status === "rejected" ? (prompt(t("correction_review_note_prompt")) || "") : "";
  try {
    const response = await fetch(apiUrl(`/api/attendance/corrections/${correctionId}/review`), {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${apiToken}` },
      body: JSON.stringify({ status, review_note: note })
    });
    const data = await readJsonSafely(response);
    if (!response.ok) {
      alert(`${t("action_failed")} ${data.detail || response.status}`);
      return;
    }
    addAudit(status === "approved" ? "approve_leave_action" : "reject_leave_action");
    renderAttendance();
  } catch (error) {
    alert(`${t("backend_unavailable")} ${error.message || ""}`);
  }
}

async function submitAttendanceCorrection() {
  const dateValue = $("correctionDate").value;
  const reason = $("correctionReason").value.trim();
  if (!dateValue || !reason) {
    $("correctionMessage").textContent = t("correction_required");
    return;
  }
  const item = (window.__emeraldAttendance || []).find(row => row.work_date === dateValue);
  if (CONFIG.API_BASE_URL && apiToken && item?.id) {
    try {
      const response = await fetch(apiUrl(`/api/attendance/${item.id}/corrections`), {
        method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${apiToken}` },
        body: JSON.stringify({ requested_clock_in: $("correctionClockIn").value || null, requested_clock_out: $("correctionClockOut").value || null, reason })
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
    } catch (error) {
      console.info("Attendance correction API unavailable; storing locally.", error);
    }
  }
  const key = `${STORAGE.attendanceCorrections}_${current.id}`;
  const corrections = JSON.parse(localStorage.getItem(key) || "[]");
  corrections.push({ date: dateValue, clockIn: $("correctionClockIn").value, clockOut: $("correctionClockOut").value, reason, status: "pending", at: new Date().toISOString() });
  localStorage.setItem(key, JSON.stringify(corrections));
  $("correctionMessage").textContent = t("correction_submitted");
  addAudit("attendance_correction_action");
}

function exportAttendance() {
  const items = window.__emeraldAttendance || [];
  downloadCSV("attendance_records.csv", [
    [t("date"), t("scheduled_time"), t("clock_in"), t("clock_out"), t("attendance_status"), t("attendance_source")],
    ...items.map(item => [item.work_date, `${item.scheduled_start || ""}-${item.scheduled_end || ""}`, item.clock_in || "", item.clock_out || "", t(ATTENDANCE_STATUS_KEYS[item.status] || "no_data"), item.source || ""])
  ]);
}

function onboardingKey() {
  return `${STORAGE.onboarding}_${current?.id || "guest"}`;
}

function loadOnboardingState() {
  try {
    const value = JSON.parse(localStorage.getItem(onboardingKey()) || "{}");
    return value && typeof value === "object" ? value : {};
  } catch (error) {
    console.info("Unable to load onboarding progress.", error);
    return {};
  }
}

function saveOnboardingState(state) {
  localStorage.setItem(onboardingKey(), JSON.stringify(state));
}

function renderOnboarding() {
  const checklist = $("onboardingChecklist");
  const cards = $("policyCards");
  if (!checklist || !cards) return;
  const config = loadContentConfig();
  const state = loadOnboardingState();
  checklist.innerHTML = config.onboardingItems.map(item => {
    const checked = Boolean(state[item.id]);
    return `<label class="check-item ${checked ? "done" : ""}">` +
      `<input type="checkbox" data-onboarding-id="${escapeHtml(item.id)}" ${checked ? "checked" : ""}>` +
      `<span>${escapeHtml(managedText(item))}</span></label>`;
  }).join("");
  checklist.querySelectorAll("[data-onboarding-id]").forEach(input => {
    input.onchange = () => {
      const next = loadOnboardingState();
      next[input.dataset.onboardingId] = input.checked;
      saveOnboardingState(next);
      renderOnboarding();
    };
  });
  const done = config.onboardingItems.filter(item => state[item.id]).length;
  const percent = config.onboardingItems.length ? Math.round((done / config.onboardingItems.length) * 100) : 0;
  if ($("onboardingProgressText")) $("onboardingProgressText").textContent = t("onboarding_progress", { done, total: config.onboardingItems.length });
  if ($("onboardingProgressBar")) $("onboardingProgressBar").style.width = `${percent}%`;

  cards.innerHTML = POLICY_CARDS.map(([title, body]) =>
    `<article class="policy-card"><span class="badge pending">${escapeHtml(t("policy_draft"))}</span>` +
    `<h4>${escapeHtml(t(title))}</h4><p>${escapeHtml(t(body))}</p>` +
    `<button class="soft" type="button" data-policy-question="${escapeHtml(title)}">${escapeHtml(t("ask_policy_ai"))}</button></article>`
  ).join("");
  cards.querySelectorAll("[data-policy-question]").forEach(button => {
    button.onclick = () => openOnboardingAI(button.dataset.policyQuestion);
  });
  renderOnboardingManager(config);
}

function openOnboardingAI(topicKey = "") {
  showPage("ai");
  const topic = topicKey ? t(topicKey) : "";
  $("aiInput").value = topic ? `${t("onboarding_ai_question")} ${topic}` : t("onboarding_ai_question");
  $("aiInput").focus();
}

function resetOnboarding() {
  localStorage.removeItem(onboardingKey());
  renderOnboarding();
}

async function boot() {
  fillLanguageSelectors();
  bindEvents();
  applyTheme(readStored(STORAGE.theme, LEGACY_STORAGE.theme) || "light");
  await setLanguage(lang);
  renderBars();
  await loadHolidays(calendarCursor.getFullYear());
  renderCalendar();
  setDefaultDates();
  await updateLeaveCalculation();
  renderAIConversation();
  updateAIStatus();
  renderOnboarding();
  renderSops();
  renderSopQuiz();
  renderEnterpriseKpis();
  renderNotifications();
  const saved = sessionStorage.getItem(STORAGE.user) || sessionStorage.getItem(LEGACY_STORAGE.user);
  if (saved && apiToken && CONFIG.API_BASE_URL) {
    try {
      const response = await fetch(apiUrl("/api/me"), {
        headers: { Authorization: `Bearer ${apiToken}` }
      });
      if (response.ok) {
        const data = await response.json();
        USERS[data.id] = {
          name: data.name, role: data.role,
          department: data.department || "General",
          rotationGroup: data.rotation_group || "NONE",
          photo: data.photo_data || null
        };
        enterApp(data.id, false);
        return;
      }
      if (response.status === 401 || response.status === 403) {
        apiToken = "";
        sessionStorage.removeItem(STORAGE.token);
        sessionStorage.removeItem(STORAGE.user);
        return;
      }
    } catch (error) {
      console.info("Could not refresh session from /api/me, falling back to cached data.", error);
    }
  }
  if (saved && USERS[saved]) enterApp(saved, false);
}

function fillLanguageSelectors() {
  const fallbackNames = { "zh-TW": "繁體中文", en: "English", th: "ไทย" };
  ["loginLanguage", "topLanguage", "settingsLanguage"].forEach(id => {
    const element = $(id);
    if (!element) return;
    SUPPORTED_LANGUAGES.forEach(code => {
      let option = Array.from(element.options).find(item => item.value === code);
      if (!option) {
        option = document.createElement("option");
        option.value = code;
        element.appendChild(option);
      }
      option.textContent = I18N[code]?.name || fallbackNames[code];
    });
    Array.from(element.options).forEach(option => {
      if (!SUPPORTED_LANGUAGES.includes(option.value)) option.remove();
    });
    element.value = SUPPORTED_LANGUAGES.includes(lang) ? lang : "zh-TW";
    if (element.selectedIndex < 0) element.selectedIndex = 0;
  });
  updateLanguageQuickButtons();
}

function updateLanguageQuickButtons() {
  document.querySelectorAll("[data-language-choice]").forEach(button => {
    const active = button.dataset.languageChoice === lang;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", active ? "true" : "false");
  });
}

async function refreshLanguageSection(name, callback) {
  try {
    await callback();
  } catch (error) {
    console.error(`[i18n] Failed to refresh ${name}.`, error);
  }
}

async function setLanguage(code) {
  lang = SUPPORTED_LANGUAGES.includes(code) ? code : "zh-TW";
  localStorage.setItem(STORAGE.language, lang);
  dict = I18N[lang] || I18N["zh-TW"] || I18N.en || {};
  document.documentElement.lang = lang;
  document.documentElement.dir = "ltr";
  document.title = t("page_title");

  // Translate all static UI first. Dynamic navigation buttons also carry
  // data-i18n attributes, so their labels change even if a later renderer fails.
  document.querySelectorAll("[data-i18n]").forEach(element => {
    element.textContent = t(element.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach(element => {
    element.placeholder = t(element.dataset.i18nPlaceholder);
  });
  document.querySelectorAll("[data-i18n-aria-label]").forEach(element => {
    element.setAttribute("aria-label", t(element.dataset.i18nAriaLabel));
  });
  ["loginLanguage", "topLanguage", "settingsLanguage"].forEach(id => {
    if ($(id)) $(id).value = lang;
  });
  updateLanguageQuickButtons();

  // Update the dynamic shell before refreshing page content. Previously these
  // updates happened last, so one stale-data rendering error could leave the
  // sidebar and role label in Chinese while the page body changed to English.
  if (current) {
    const activePage = document.querySelector(".page.active")?.dataset.page || "dashboard";
    buildNav();
    $("userRole").textContent = t(current.role);
    const item = NAV.find(entry => entry[0] === activePage);
    $("pageTitle").textContent = t(item ? item[1] : activePage);
  }

  const refreshers = [
    ["calendar weekdays", () => renderCalendarWeekdays()],
    ["dashboard charts", () => renderBars()],
    ["holiday sync status", () => renderHolidaySyncStatus(holidayLoadedFrom)],
    ["holiday table", () => renderHolidayTable()],
    ["next holiday", () => renderNextHoliday()],
    ["calendar", () => renderCalendar()],
    ["rotation", () => renderRotationPage()],
    ["leave calculation", () => updateLeaveCalculation()],
    ["audit log", () => renderAudit()],
    ["AI conversation", () => renderAIConversation()],
    ["AI status", () => updateAIStatus()],
    ["onboarding", () => renderOnboarding()],
    ["SOP modules", () => renderSops()],
    ["SOP quiz", () => renderSopQuiz()],
    ["enterprise KPIs", () => renderEnterpriseKpis()],
    ["notifications", () => renderNotifications()]
  ];

  if (current) {
    refreshers.push(
      ["leave requests", () => renderRequests()],
      ["attendance", () => renderAttendance()],
      ["dashboard counters", () => updateCounts()]
    );
  }

  for (const [name, callback] of refreshers) {
    await refreshLanguageSection(name, callback);
  }
}

function bindEvents() {
  $("loginButton").onclick = login;
  $("logoutButton").onclick = () => {
    addAudit("logout_action");
    sessionStorage.clear();
    location.reload();
  };
  ["loginLanguage", "topLanguage", "settingsLanguage"].forEach(id => {
    $(id).onchange = event => {
      void setLanguage(event.target.value).catch(error => {
        console.error("Unable to change language.", error);
      });
    };
  });
  document.querySelectorAll("[data-language-choice]").forEach(button => {
    button.onclick = () => setLanguage(button.dataset.languageChoice);
  });
  $("themeButton").onclick = toggleTheme;
  $("themeSelect").onchange = event => applyTheme(event.target.value);
  $("submitLeave").onclick = submitLeave;
  $("startDate").onchange = updateLeaveCalculation;
  $("endDate").onchange = updateLeaveCalculation;
  $("saveRotation").onclick = saveRotationSettings;
  $("addRotationOverride").onclick = addRotationOverride;
  $("exportRequests").onclick = () => downloadCSV(
    "leave_requests.csv",
    [
      ["ID", t("employee"), t("type"), t("date"), t("deducted_days"), t("status")],
      ...requests.map(request => [request.id, request.user, t(request.type), request.date, request.workdays || 0, t(request.status)])
    ]
  );
  $("exportReport").onclick = () => exportMonthlyReport();
  $("downloadTemplate").onclick = () => downloadExcelTemplate();
  $("fakeImport").onclick = () => parseExcelFile();
  $("confirmExcelImport").onclick = () => confirmExcelImport();
  $("excelImportType").onchange = () => {
    updateExcelImportHelp();
    $("excelPreviewWrap").classList.add("hidden");
    $("confirmExcelImport").classList.add("hidden");
    $("excelMessage").textContent = "";
    excelParsedRows = [];
  };
  updateExcelImportHelp();
  $("aiSend").onclick = sendAI;
  $("aiClear").onclick = clearAIChat;
  $("resetOnboarding").onclick = resetOnboarding;
  $("askOnboardingAI").onclick = () => openOnboardingAI();
  $("toggleOnboardingManager").onclick = () => toggleManagerPanel("onboardingManager", "toggleOnboardingManager");
  $("saveOnboardingItem").onclick = saveOnboardingContentItem;
  $("cancelOnboardingEdit").onclick = () => { clearOnboardingEditor(); setContentManagerMessage("onboardingManagerMessage", ""); };
  $("restoreOnboardingDefaults").onclick = restoreDefaultOnboardingContent;
  $("sopSearch").oninput = renderSops;
  $("sopCategory").onchange = renderSops;
  $("submitSopQuiz").onclick = submitSopQuiz;
  $("toggleQuizManager").onclick = () => toggleManagerPanel("quizManager", "toggleQuizManager");
  $("saveQuizQuestion").onclick = saveQuizQuestion;
  $("cancelQuizEdit").onclick = () => { clearQuizEditor(); setContentManagerMessage("quizManagerMessage", ""); };
  $("saveQuizPassingScore").onclick = saveQuizPassingScore;
  $("restoreQuizDefaults").onclick = restoreDefaultQuizContent;
  $("attendanceExport").onclick = exportAttendance;
  $("submitCorrection").onclick = submitAttendanceCorrection;
  if ($("markNotificationsRead")) $("markNotificationsRead").onclick = markAllNotificationsRead;
  $("aiInput").onkeydown = event => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendAI();
    }
  };
  document.querySelectorAll("[data-ai-question]").forEach(button => {
    button.onclick = () => {
      $("aiInput").value = t(button.dataset.aiQuestion);
      sendAI();
    };
  });
  $("syncHoliday").onclick = syncHolidays;
  $("prevYear").onclick = () => changeCalendarYear(-1);
  $("prevMonth").onclick = () => changeCalendarMonth(-1);
  $("nextMonth").onclick = () => changeCalendarMonth(1);
  $("nextYear").onclick = () => changeCalendarYear(1);
  $("todayMonth").onclick = goToCurrentMonth;
  $("saveSettings").onclick = () => {
    $("settingsMessage").textContent = t("saved");
    applyTheme($("themeSelect").value);
  };
  $("changePasswordButton").onclick = async () => {
    const messageEl = $("changePasswordMessage");
    const currentPassword = $("currentPasswordInput").value;
    const newPassword = $("newPasswordInput").value;
    const confirmPassword = $("confirmNewPasswordInput").value;

    if (!currentPassword || !newPassword) {
      messageEl.textContent = t("password_fields_required");
      return;
    }
    if (newPassword.length < 8) {
      messageEl.textContent = t("password_too_short");
      return;
    }
    if (newPassword !== confirmPassword) {
      messageEl.textContent = t("password_mismatch");
      return;
    }
    if (!CONFIG.API_BASE_URL || !apiToken) {
      messageEl.textContent = t("backend_unavailable");
      return;
    }

    messageEl.textContent = "…";
    try {
      const response = await fetch(apiUrl("/api/me/change-password"), {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${apiToken}` },
        body: JSON.stringify({ current_password: currentPassword, new_password: newPassword })
      });
      if (response.ok) {
        messageEl.textContent = t("password_changed_success");
        $("currentPasswordInput").value = "";
        $("newPasswordInput").value = "";
        $("confirmNewPasswordInput").value = "";
      } else if (response.status === 401 || response.status === 403) {
        messageEl.textContent = t("current_password_incorrect");
      } else {
        messageEl.textContent = t("password_change_failed");
      }
    } catch (error) {
      console.info("Change password failed.", error);
      messageEl.textContent = t("password_change_failed");
    }
  };
  $("globalSearch").oninput = event => searchNav(event.target.value);
  document.querySelectorAll("[data-go]").forEach(button => {
    button.onclick = () => showPage(button.dataset.go);
  });
}

async function login() {
  const id = $("loginId").value.trim().toUpperCase();
  const password = $("loginPassword").value;
  $("loginError").textContent = "";

  if (CONFIG.API_BASE_URL) {
    try {
      const response = await fetch(apiUrl("/api/auth/login"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ account: id, password })
      });
      if (response.ok) {
        const data = await response.json();
        apiToken = data.access_token;
        sessionStorage.setItem(STORAGE.token, apiToken);
        USERS[data.user.id] = {
          name: data.user.name, role: data.user.role,
          department: data.user.department || "General",
          rotationGroup: data.user.rotation_group || "NONE",
          photo: data.user.photo_data || null
        };
        enterApp(data.user.id);
        return;
      }
      if (response.status === 403) {
        $("loginError").textContent = t("account_deactivated");
        return;
      }
      if (response.status === 401) {
        $("loginError").textContent = t("invalid_credentials");
        return;
      }
      if (CONFIG.APP_MODE === "production") {
        $("loginError").textContent = t("backend_unavailable");
        return;
      }
    } catch (error) {
      console.info("Backend login unavailable.", error);
      if (CONFIG.APP_MODE === "production") {
        $("loginError").textContent = t("backend_unavailable");
        return;
      }
    }
  } else if (CONFIG.APP_MODE === "production") {
    $("loginError").textContent = t("production_login_required");
    return;
  }

  if (!USERS[id] || password !== "1234") {
    $("loginError").textContent = t("invalid_credentials");
    return;
  }
  enterApp(id);
}

function enterApp(id, recordAudit = true) {
  current = { id, ...USERS[id] };
  sessionStorage.setItem(STORAGE.user, id);
  $("loginView").classList.add("hidden");
  $("appView").classList.remove("hidden");
  $("userName").textContent = `${id} ${current.name}`;
  $("userRole").textContent = t(current.role);
  if (current.photo) {
    $("userPhoto").src = current.photo;
    $("userPhoto").classList.remove("hidden");
  } else {
    $("userPhoto").classList.add("hidden");
  }
  buildNav();
  renderRequests();
  if (CONFIG.API_BASE_URL && apiToken) {
    loadLeaveRequestsFromBackend();
  }
  renderAudit();
  renderHolidayTable();
  renderRotationPage();
  renderCalendar();
  renderOnboarding();
  renderSops();
  renderSopQuiz();
  renderAttendance();
  renderEnterpriseKpis();
  renderNotifications();
  updateLeaveCalculation();
  updateCounts();
  if (CONFIG.API_BASE_URL && apiToken) loadRotationFromBackend().catch(error => console.info("Rotation settings unavailable.", error));
  refreshBackendSops().then(() => { renderSops(); renderSopQuiz(); renderEnterpriseKpis(); }).catch(() => {});
  if (recordAudit) addAudit("login_action");
}

function buildNav() {
  const activePage = document.querySelector(".page.active")?.dataset.page || "dashboard";
  $("mainNav").innerHTML = "";
  NAV.filter(entry => entry[2].includes(current.role)).forEach(([page, key]) => {
    const button = document.createElement("button");
    button.dataset.page = page;
    button.dataset.i18n = key;
    if (page === activePage) button.classList.add("active");
    button.textContent = t(key);
    button.onclick = () => showPage(page);
    $("mainNav").appendChild(button);
  });
  if (current.role === "hr" || current.role === "admin") {
    const rulesButton = document.createElement("button");
    rulesButton.dataset.i18n = "rules_admin";
    rulesButton.textContent = t("rules_admin");
    rulesButton.onclick = () => window.open("./admin_rules.html", "_blank");
    $("mainNav").appendChild(rulesButton);

    const sopsButton = document.createElement("button");
    sopsButton.dataset.i18n = "sops_admin";
    sopsButton.textContent = t("sops_admin");
    sopsButton.onclick = () => window.open("./admin_sops.html", "_blank");
    $("mainNav").appendChild(sopsButton);
  }
  renderNotificationNavBadge();
}

function showPage(page) {
  document.querySelectorAll(".page").forEach(element => {
    element.classList.toggle("active", element.dataset.page === page);
  });
  document.querySelectorAll("#mainNav button").forEach(button => {
    button.classList.toggle("active", button.dataset.page === page);
  });
  const item = NAV.find(entry => entry[0] === page);
  $("pageTitle").textContent = t(item ? item[1] : page);
  if (page === "requests") renderRequests();
  if (page === "audit") renderAudit();
  if (page === "calendar") renderCalendar();
  if (page === "rotation") renderRotationPage();
  if (page === "onboarding") renderOnboarding();
  if (page === "sops") {
    renderSops();
    renderSopQuiz();
    refreshBackendSops().then(() => { renderSops(); renderEnterpriseKpis(); }).catch(() => {});
  }
  if (page === "attendance") renderAttendance();
  if (page === "notifications") renderNotifications();
  if (page === "apply") updateLeaveCalculation();
}

function searchNav(query) {
  const normalized = query.toLowerCase().trim();
  document.querySelectorAll("#mainNav button").forEach(button => {
    button.style.display = button.textContent.toLowerCase().includes(normalized) ? "" : "none";
  });
}

function toggleTheme() {
  applyTheme(document.body.classList.contains("dark") ? "light" : "dark");
}

function applyTheme(theme) {
  const selected = theme === "dark" ? "dark" : "light";
  document.body.classList.toggle("dark", selected === "dark");
  localStorage.setItem(STORAGE.theme, selected);
  if ($("themeSelect")) $("themeSelect").value = selected;
}

function setDefaultDates() {
  const date = new Date();
  date.setDate(date.getDate() + 1);
  const value = localIsoDate(date);
  $("startDate").value = value;
  $("endDate").value = value;
}

async function updateLeaveCalculation() {
  const container = $("leaveCalculation");
  if (!container) return null;
  const start = $("startDate").value;
  const end = $("endDate").value;
  if (!start || !end || end < start) {
    lastLeaveCalculation = null;
    container.innerHTML = `<strong>${escapeHtml(t("leave_calculation"))}</strong><p>${escapeHtml(t("invalid_date"))}</p>`;
    return null;
  }
  let result = null;
  if (CONFIG.API_BASE_URL && apiToken) {
    try {
      const response = await fetch(apiUrl("/api/leaves/calculate"), {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${apiToken}` },
        body: JSON.stringify({ start_date: start, end_date: end })
      });
      if (response.ok) result = await response.json();
    } catch (error) {
      console.info("Backend leave calculation unavailable; using browser calculation.", error);
    }
  }
  result ||= calculateDemoLeave(start, end);
  lastLeaveCalculation = result;
  if (!result) return null;
  container.innerHTML =
    `<strong>${escapeHtml(t("leave_calculation"))}</strong>` +
    `<div class="calculation-grid">` +
    `<span>${escapeHtml(t("calendar_days"))}<b>${result.calendar_days}</b></span>` +
    `<span>${escapeHtml(t("rotation_days_off"))}<b>${result.rotation_days_off || 0}</b></span>` +
    `<span>${escapeHtml(t("holidays_excluded"))}<b>${result.holidays || 0}</b></span>` +
    `<span class="deduct-total">${escapeHtml(t("actual_deduction"))}<b>${result.workdays}</b></span>` +
    `</div><small>${escapeHtml(t("rotation_group_value", { group: result.rotation_group }))}</small>`;
  return result;
}

async function submitLeave() {
  const start = $("startDate").value;
  const end = $("endDate").value;
  if (!start || !end || end < start) {
    $("applyMessage").textContent = t("invalid_date");
    return;
  }
  const calculation = await updateLeaveCalculation();
  if (!calculation || calculation.workdays <= 0) {
    $("applyMessage").textContent = t("no_workdays_selected");
    return;
  }

  let created = null;
  if (CONFIG.API_BASE_URL && apiToken) {
    try {
      const response = await fetch(apiUrl("/api/leaves"), {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${apiToken}` },
        body: JSON.stringify({
          leave_type: $("leaveType").value,
          start_date: start,
          end_date: end,
          reason: $("reason").value
        })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || `HTTP ${response.status}`);
      created = data;
    } catch (error) {
      if (CONFIG.APP_MODE === "production") {
        $("applyMessage").textContent = `${t("backend_unavailable")}: ${error.message}`;
        return;
      }
      console.info("Leave API unavailable; saving demo request.", error);
    }
  }

  requests.unshift({
    id: created?.id || Date.now(),
    user: `${current.id} ${current.name}`,
    type: $("leaveType").value,
    date: start === end ? start : `${start} ~ ${end}`,
    workdays: Number(created?.workdays ?? calculation.workdays),
    status: created?.status || "manager_pending"
  });
  saveRequests();
  addAudit("submit_leave_action", `${calculation.workdays} ${t("days_unit")}`);
  $("applyMessage").textContent = `✓ ${t("leave_submitted_with_days", { days: calculation.workdays })}`;
  renderRequests();
  updateCounts();
}

function renderRequests() {
  if (!current) return;
  const list = current.role === "employee"
    ? requests.filter(request => request.user.startsWith(current.id))
    : requests;
  $("requestRows").innerHTML = list.map(request => {
    let actions = "";
    if (current.role === "manager" && request.status === "manager_pending") {
      actions = `<button class="soft" onclick="approveRequest(${Number(request.id)},'manager')">${escapeHtml(t("approve"))}</button>` +
        `<button class="ghost" onclick="rejectRequest(${Number(request.id)})">${escapeHtml(t("reject"))}</button>`;
    }
    if (["hr", "admin"].includes(current.role) && request.status === "hr_pending") {
      actions = `<button class="primary" onclick="approveRequest(${Number(request.id)},'hr')">${escapeHtml(t("approve"))}</button>` +
        `<button class="ghost" onclick="rejectRequest(${Number(request.id)})">${escapeHtml(t("reject"))}</button>`;
    }
    return `<tr>` +
      `<td>${escapeHtml(request.id)}</td>` +
      `<td>${escapeHtml(request.user)}</td>` +
      `<td>${escapeHtml(t(request.type))}</td>` +
      `<td>${escapeHtml(request.date)}</td>` +
      `<td>${escapeHtml(request.workdays || 0)}</td>` +
      `<td><span class="badge ${statusClass(request.status)}">${escapeHtml(t(request.status))}</span></td>` +
      `<td><div class="row-actions">${actions}</div></td>` +
      `</tr>`;
  }).join("") || `<tr><td colspan="7">${escapeHtml(t("no_data"))}</td></tr>`;
}

function mapBackendLeaveToLocal(item) {
  const employeeName = USERS[item.employee_id]?.name;
  const date = item.start_date === item.end_date
    ? item.start_date
    : `${item.start_date} ~ ${item.end_date}`;
  return {
    id: item.id,
    user: employeeName ? `${item.employee_id} ${employeeName}` : item.employee_id,
    type: LEAVE_TYPE_ALIASES[item.leave_type] || item.leave_type || "annual_leave",
    date,
    workdays: Number(item.workdays || 0),
    status: item.status
  };
}

async function loadLeaveRequestsFromBackend() {
  try {
    const response = await fetch(apiUrl("/api/leaves"), {
      headers: { Authorization: `Bearer ${apiToken}` }
    });
    if (!response.ok) return;
    const data = await response.json();
    if (!Array.isArray(data)) return;
    requests = data.map(mapBackendLeaveToLocal);
    saveRequests();
    renderRequests();
    updateCounts();
  } catch (error) {
    console.info("Could not refresh leave requests from backend; showing cached data.", error);
  }
}

window.approveRequest = async (id, stage) => {
  const request = requests.find(item => Number(item.id) === Number(id));
  if (!request) return;

  if (CONFIG.API_BASE_URL && apiToken) {
    const path = stage === "manager"
      ? `/api/leaves/${id}/manager-approve`
      : `/api/leaves/${id}/hr-approve`;
    try {
      const response = await fetch(apiUrl(path), {
        method: "POST",
        headers: { Authorization: `Bearer ${apiToken}` }
      });
      const data = await readJsonSafely(response);
      if (!response.ok) {
        alert(`${t("action_failed")} ${data.detail || response.status}`);
        return;
      }
      Object.assign(request, mapBackendLeaveToLocal(data));
    } catch (error) {
      alert(`${t("backend_unavailable")} ${error.message || ""}`);
      return;
    }
  } else {
    request.status = stage === "manager" ? "hr_pending" : "approved";
  }

  saveRequests();
  addAudit("approve_leave_action");
  renderRequests();
  updateCounts();
};

window.rejectRequest = async id => {
  const request = requests.find(item => Number(item.id) === Number(id));
  if (!request) return;

  if (CONFIG.API_BASE_URL && apiToken) {
    try {
      const response = await fetch(apiUrl(`/api/leaves/${id}/reject`), {
        method: "POST",
        headers: { Authorization: `Bearer ${apiToken}` }
      });
      const data = await readJsonSafely(response);
      if (!response.ok) {
        alert(`${t("action_failed")} ${data.detail || response.status}`);
        return;
      }
      Object.assign(request, mapBackendLeaveToLocal(data));
    } catch (error) {
      alert(`${t("backend_unavailable")} ${error.message || ""}`);
      return;
    }
  } else {
    request.status = "rejected";
  }

  saveRequests();
  addAudit("reject_leave_action");
  renderRequests();
  updateCounts();
};

function statusClass(status) {
  return status === "approved" ? "approved" : status === "rejected" ? "rejected" : "pending";
}

function saveRequests() {
  localStorage.setItem(STORAGE.requests, JSON.stringify(requests));
}

function updateCounts() {
  $("pendingCount").textContent = requests.filter(request => String(request.status).includes("pending")).length;
}

function addAudit(action, detail = "") {
  if (!current) return;
  audits.unshift({
    time: new Date().toISOString(),
    user: current.id,
    action,
    detail
  });
  audits = audits.slice(0, 100);
  localStorage.setItem(STORAGE.audits, JSON.stringify(audits));
  renderAudit();
}

function gregorianLocale() {
  // "th" locale defaults to the Buddhist Era calendar (year + 543) in
  // toLocaleDateString/toLocaleString. We display the Gregorian year as the
  // primary year everywhere (matches backend dates, holiday sync, etc.) and
  // separately append the Buddhist Era year for Thai-language users via
  // buddhistYearSuffix(), rather than letting the browser silently swap
  // which calendar is shown.
  return lang === "th" ? "th-TH-u-ca-gregory" : lang;
}

function buddhistYearSuffix(date) {
  return lang === "th" ? ` (พ.ศ. ${date.getFullYear() + 543})` : "";
}

function formatWithBuddhistYear(date, { dateOnly = false } = {}) {
  const text = dateOnly
    ? date.toLocaleDateString(gregorianLocale())
    : date.toLocaleString(gregorianLocale());
  return text + buddhistYearSuffix(date);
}

function formatAuditTime(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? String(value || "") : date.toLocaleString(gregorianLocale()) + buddhistYearSuffix(date);
}

function renderAudit() {
  if (!$("auditRows")) return;
  $("auditRows").innerHTML = audits.map(item => {
    const actionKey = AUDIT_ALIASES[item.action] || item.action;
    const label = t(actionKey);
    const detail = item.detail ? ` · ${item.detail}` : "";
    return `<tr><td>${escapeHtml(formatAuditTime(item.time))}</td><td>${escapeHtml(item.user)}</td><td>${escapeHtml(label + detail)}</td></tr>`;
  }).join("") || `<tr><td colspan="3">${escapeHtml(t("no_data"))}</td></tr>`;
}

async function exportMonthlyReport() {
  const decided = requests.filter(item => item.status === "approved" || item.status === "rejected");
  const approved = requests.filter(item => item.status === "approved");
  const approvalRate = decided.length ? Math.round((approved.length / decided.length) * 100) : null;
  const averageDays = approved.length
    ? (approved.reduce((sum, item) => sum + Number(item.workdays || 0), 0) / approved.length)
    : null;

  let totalEmployees = null;
  if (CONFIG.API_BASE_URL && apiToken && (current?.role === "hr" || current?.role === "admin")) {
    try {
      const response = await fetch(apiUrl("/api/admin/users"), {
        headers: { Authorization: `Bearer ${apiToken}` }
      });
      if (response.ok) {
        const data = await response.json();
        if (Array.isArray(data)) totalEmployees = data.length;
      }
    } catch (error) {
      console.info("Could not fetch employee count for report.", error);
    }
  }

  downloadCSV("monthly_report.csv", [
    [t("total_employees_csv"), totalEmployees ?? t("not_available")],
    [t("approval_rate_csv"), approvalRate === null ? t("not_available") : `${approvalRate}%`],
    [t("average_leave_days_csv"), averageDays === null ? t("not_available") : averageDays.toFixed(1)]
  ]);
}

function downloadCSV(filename, rows) {
  const csv = "\ufeff" + rows.map(row => row.map(value =>
    `"${String(value).replaceAll('"', '""')}"`
  ).join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const anchor = document.createElement("a");
  anchor.href = URL.createObjectURL(blob);
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(anchor.href);
  addAudit("export_action", filename);
}

let excelParsedRows = [];
const EXCEL_VALID_ROLES = ["employee", "manager", "hr", "admin"];
const EXCEL_VALID_ROTATIONS = ["A", "B", "NONE"];
const EXCEL_VALID_ATTENDANCE_STATUS = ["normal", "late", "early_leave", "missing_punch", "absent", "day_off"];

function parseCsvText(text) {
  return text.split(/\r?\n/)
    .map(line => line.trim())
    .filter(Boolean)
    .map(line => line.split(",").map(cell => cell.replace(/^"|"$/g, "").trim()));
}

function normalizeEmployeeRow(cells) {
  const [id, name, role, department, rotation, password] = cells;
  const normalizedRole = (role || "").trim().toLowerCase();
  const normalizedRotation = (rotation || "").trim().toUpperCase();
  return {
    id: (id || "").trim().toUpperCase(),
    name: (name || "").trim(),
    role: EXCEL_VALID_ROLES.includes(normalizedRole) ? normalizedRole : "employee",
    department: (department || "").trim() || "General",
    rotation_group: EXCEL_VALID_ROTATIONS.includes(normalizedRotation) ? normalizedRotation : "NONE",
    password: (password || "").trim() || crypto.randomUUID().replace(/-/g, "").slice(0, 12)
  };
}

function normalizeAttendanceRow(cells) {
  const [employeeId, workDate, scheduledStart, scheduledEnd, clockIn, clockOut, status, source, note] = cells;
  const normalizedStatus = (status || "").trim().toLowerCase();
  return {
    employee_id: (employeeId || "").trim().toUpperCase(),
    work_date: (workDate || "").trim(),
    scheduled_start: (scheduledStart || "").trim() || "08:00",
    scheduled_end: (scheduledEnd || "").trim() || "17:00",
    clock_in: (clockIn || "").trim() || null,
    clock_out: (clockOut || "").trim() || null,
    status: EXCEL_VALID_ATTENDANCE_STATUS.includes(normalizedStatus) ? normalizedStatus : "normal",
    source: (source || "").trim() || "import",
    note: (note || "").trim()
  };
}

function readImportFileRows(file) {
  return new Promise((resolve, reject) => {
    const isCsv = /\.csv$/i.test(file.name);
    const reader = new FileReader();
    reader.onerror = () => reject(new Error(t("select_file")));
    reader.onload = () => {
      try {
        if (isCsv) {
          resolve(parseCsvText(String(reader.result)));
        } else if (window.XLSX) {
          const workbook = XLSX.read(reader.result, { type: "binary" });
          const sheet = workbook.Sheets[workbook.SheetNames[0]];
          resolve(XLSX.utils.sheet_to_json(sheet, { header: 1, raw: false, defval: "" }));
        } else {
          reject(new Error(t("excel_library_unavailable")));
        }
      } catch (error) {
        reject(error);
      }
    };
    if (isCsv) reader.readAsText(file, "utf-8");
    else reader.readAsBinaryString(file);
  });
}

function updateExcelImportHelp() {
  const isAttendance = $("excelImportType").value === "attendance";
  $("excelImportHelp").textContent = isAttendance ? t("excel_import_help_attendance") : t("excel_import_help");
}

function downloadExcelTemplate() {
  if ($("excelImportType").value === "attendance") {
    downloadCSV("attendance_import_template.csv", [
      ["employee_id", "work_date", "scheduled_start", "scheduled_end", "clock_in", "clock_out", "status", "source", "note"],
      ["E001", "2026-07-20", "08:00", "17:00", "07:56", "17:08", "normal", "device-import", ""],
      ["E002", "2026-07-20", "08:00", "17:00", "08:12", "17:03", "late", "device-import", "Traffic delay"]
    ]);
    return;
  }
  downloadCSV("employee_import_template.csv", [
    [t("employee_id"), t("name_label"), t("role"), t("department"), t("rotation"), t("initial_password")],
    ["E101", "Somchai", "employee", t("production"), "A", ""],
    ["E102", "Malee", "manager", t("production"), "B", ""]
  ]);
}

function renderExcelPreview(rows) {
  const isAttendance = $("excelImportType").value === "attendance";
  $("excelPreviewHead").innerHTML = isAttendance
    ? `<tr><th>${escapeHtml(t("employee_id"))}</th><th>${escapeHtml(t("correction_date"))}</th>` +
      `<th>${escapeHtml(t("clock_in"))}</th><th>${escapeHtml(t("clock_out"))}</th>` +
      `<th>${escapeHtml(t("attendance_status"))}</th></tr>`
    : `<tr><th>${escapeHtml(t("employee_id"))}</th><th>${escapeHtml(t("name_label"))}</th>` +
      `<th>${escapeHtml(t("role"))}</th><th>${escapeHtml(t("department"))}</th><th>${escapeHtml(t("rotation"))}</th></tr>`;

  $("excelPreviewBody").innerHTML = rows.map(row => isAttendance
    ? "<tr>" +
      `<td>${escapeHtml(row.employee_id)}</td>` +
      `<td>${escapeHtml(row.work_date)}</td>` +
      `<td>${escapeHtml(row.clock_in || "—")}</td>` +
      `<td>${escapeHtml(row.clock_out || "—")}</td>` +
      `<td>${escapeHtml(row.status)}</td>` +
      "</tr>"
    : "<tr>" +
      `<td>${escapeHtml(row.id)}</td>` +
      `<td>${escapeHtml(row.name)}</td>` +
      `<td>${escapeHtml(row.role)}</td>` +
      `<td>${escapeHtml(row.department)}</td>` +
      `<td>${escapeHtml(row.rotation_group)}</td>` +
      "</tr>"
  ).join("");
}

async function parseExcelFile() {
  const file = $("excelFile").files[0];
  if (!file) {
    $("excelMessage").textContent = t("select_file");
    return;
  }
  const isAttendance = $("excelImportType").value === "attendance";

  try {
    const rows = await readImportFileRows(file);
    const dataRows = rows.slice(1).filter(row => row.some(cell => String(cell || "").trim()));

    excelParsedRows = isAttendance
      ? dataRows.map(normalizeAttendanceRow).filter(row => row.employee_id && /^\d{4}-\d{2}-\d{2}$/.test(row.work_date))
      : dataRows.map(normalizeEmployeeRow).filter(row => row.id && row.name);

    if (!excelParsedRows.length) {
      $("excelMessage").textContent = t("no_data");
      $("excelPreviewWrap").classList.add("hidden");
      $("confirmExcelImport").classList.add("hidden");
      return;
    }

    renderExcelPreview(excelParsedRows);
    $("excelPreviewWrap").classList.remove("hidden");
    $("confirmExcelImport").classList.remove("hidden");
    $("excelMessage").textContent = t("excel_parse_success", { count: excelParsedRows.length });
  } catch (error) {
    console.error("Failed to parse import file.", error);
    $("excelMessage").textContent = `${t("excel_parse_error")} ${error.message || ""}`;
  }
}

async function confirmEmployeeImport() {
  let created = 0;
  let skipped = 0;
  let failed = 0;
  const generatedPasswords = [];

  for (const row of excelParsedRows) {
    $("excelMessage").textContent = `${t("importing")} (${created + skipped + failed + 1} / ${excelParsedRows.length})`;
    try {
      const response = await fetch(apiUrl("/api/admin/users"), {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${apiToken}` },
        body: JSON.stringify({
          id: row.id, name: row.name, role: row.role,
          department: row.department, rotation_group: row.rotation_group,
          password: row.password
        })
      });
      if (response.status === 409) {
        skipped += 1;
      } else if (response.ok) {
        created += 1;
        generatedPasswords.push(`${row.id}: ${row.password}`);
      } else {
        failed += 1;
      }
    } catch {
      failed += 1;
    }
  }

  addAudit("excel_import_action");
  $("excelMessage").textContent = t("excel_import_summary", { created, skipped, failed });
  if (generatedPasswords.length) {
    alert(`${t("excel_import_passwords_title")}\n\n${generatedPasswords.join("\n")}\n\n${t("excel_import_passwords_note")}`);
  }
}

async function confirmAttendanceImport() {
  $("excelMessage").textContent = t("importing");
  try {
    const response = await fetch(apiUrl("/api/attendance/import"), {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${apiToken}` },
      body: JSON.stringify({ records: excelParsedRows })
    });
    const data = await readJsonSafely(response);
    if (!response.ok) {
      $("excelMessage").textContent = `${t("action_failed")} ${data.detail || response.status}`;
      return;
    }
    addAudit("excel_import_action");
    $("excelMessage").textContent = t("attendance_import_summary", {
      inserted: data.inserted ?? 0,
      updated: data.updated ?? 0
    });
  } catch (error) {
    $("excelMessage").textContent = `${t("backend_unavailable")} ${error.message || ""}`;
  }
}

async function confirmExcelImport() {
  if (!excelParsedRows.length) return;
  if (!CONFIG.API_BASE_URL || !apiToken) {
    $("excelMessage").textContent = t("backend_unavailable");
    return;
  }

  $("confirmExcelImport").disabled = true;
  if ($("excelImportType").value === "attendance") {
    await confirmAttendanceImport();
  } else {
    await confirmEmployeeImport();
  }
  $("confirmExcelImport").disabled = false;
  $("confirmExcelImport").classList.add("hidden");
  $("excelPreviewWrap").classList.add("hidden");
  excelParsedRows = [];
  $("excelFile").value = "";
}

function renderBars() {
  if (!$("trendBars") || !$("reportBars")) return;
  const formatter = new Intl.DateTimeFormat(lang, { month: "short" });
  const months = Array.from({ length: 6 }, (_, index) => formatter.format(new Date(2026, index, 1)));
  const values = [45, 70, 58, 82, 64, 76];
  $("trendBars").innerHTML = values.map((value, index) =>
    `<div class="bar" style="height:${value}%"><span>${escapeHtml(months[index])}</span></div>`
  ).join("");

  const renderReportBars = values => {
    if (!$("reportBars")) return;
    $("reportBars").innerHTML = values.map((value, index) =>
      `<div class="bar" style="height:${value}%"><span>${escapeHtml(t("day_prefix", { value: index + 1 }))}</span></div>`
    ).join("");
  };

  if (CONFIG.API_BASE_URL && apiToken) {
    const today = new Date();
    const days = Array.from({ length: 8 }, (_, index) => {
      const day = new Date(today);
      day.setDate(day.getDate() - (7 - index));
      return localIsoDate(day);
    });
    Promise.all(days.map(day =>
      fetch(apiUrl(`/api/attendance/summary?start_date=${day}&end_date=${day}`), { headers: { Authorization: `Bearer ${apiToken}` } })
        .then(response => response.ok ? response.json() : null)
        .then(summary => summary ? summary.normal_rate : null)
        .catch(() => null)
    )).then(rates => {
      if (rates.every(rate => rate === null)) { renderReportBars([55, 75, 48, 86, 67, 72, 60, 89]); return; }
      renderReportBars(rates.map(rate => rate === null ? 0 : rate));
    });
  } else {
    renderReportBars([55, 75, 48, 86, 67, 72, 60, 89]);
  }
}

function holidayDate(item) {
  return String(item?.date || "").slice(0, 10);
}

function holidayCacheKey(year) {
  return `${HOLIDAY_CACHE_PREFIX}${year}`;
}

function extractHolidaySuffixes(name) {
  let base = String(name || "").trim();
  const suffixes = [];
  const patterns = [
    ["（補假）", "substitute"],
    ["(補假)", "substitute"],
    ["（僅曼谷）", "bangkok_only"],
    ["(僅曼谷)", "bangkok_only"]
  ];
  let changed = true;
  while (changed) {
    changed = false;
    for (const [text, code] of patterns) {
      if (base.endsWith(text)) {
        base = base.slice(0, -text.length).trim();
        suffixes.unshift(code);
        changed = true;
        break;
      }
    }
  }
  return { base, suffixes };
}

function buildHolidayNames(name) {
  const cleaned = String(name || "")
    .replace(/[（(][^）)]*[A-Za-z][^）)]*[）)]/g, "")
    .replace(/\s+/g, " ")
    .trim();
  const { base, suffixes } = extractHolidaySuffixes(cleaned);
  const known = HOLIDAY_TRANSLATIONS[base] || { "zh-TW": base, en: base, th: base };
  const names = { ...known };
  for (const suffix of suffixes) {
    if (suffix === "substitute") {
      names["zh-TW"] += "（補假）";
      names.en += " (substitute holiday)";
      names.th += " (วันหยุดชดเชย)";
    } else if (suffix === "bangkok_only") {
      names["zh-TW"] += "（僅曼谷）";
      names.en += " (Bangkok only)";
      names.th += " (เฉพาะกรุงเทพฯ)";
    }
  }
  return names;
}

function displayHolidayName(item) {
  const names = item?.names && typeof item.names === "object" ? item.names : buildHolidayNames(item?.name);
  return String(names[lang] || names["zh-TW"] || item?.name || "").trim();
}

function reviewStatusText(item) {
  return item.company_confirmed ? t("confirmed") : t("pending_hr_review");
}

function normalizeHolidays(items) {
  return (Array.isArray(items) ? items : [])
    .filter(item => /^\d{4}-\d{2}-\d{2}$/.test(holidayDate(item)) && item.name)
    .map(item => ({ ...item, names: item.names || buildHolidayNames(item.name) }))
    .sort((a, b) => holidayDate(a).localeCompare(holidayDate(b)));
}

function readHolidayCache(year) {
  try {
    return normalizeHolidays(JSON.parse(localStorage.getItem(holidayCacheKey(year)) || "[]"));
  } catch (error) {
    console.info("Holiday cache cannot be read.", error);
    return [];
  }
}

function writeHolidayCache(year, items) {
  try {
    localStorage.setItem(holidayCacheKey(year), JSON.stringify(items));
  } catch (error) {
    console.info("Holiday cache is unavailable.", error);
  }
}

async function loadStaticHolidayData(year) {
  const url = new URL(`./data/holidays/${year}.json`, document.baseURI);
  url.searchParams.set("v", Date.now().toString());
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) throw new Error(`Static holiday JSON HTTP ${response.status}`);
  const payload = await response.json();
  const items = Array.isArray(payload) ? payload : payload.holidays;
  return { items: normalizeHolidays(items), meta: Array.isArray(payload) ? {} : payload };
}

async function loadHolidays(year) {
  let loadedFrom = "offline";
  holidayDataMeta = {};
  let lastError = null;

  if (CONFIG.API_BASE_URL) {
    try {
      const response = await fetch(apiUrl(`/api/holidays?year=${year}&country=TH`), { cache: "no-store" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      holidays = normalizeHolidays(await response.json());
      writeHolidayCache(year, holidays);
      loadedFrom = "api";
    } catch (error) {
      lastError = error;
    }
  }

  if (loadedFrom !== "api" && location.protocol !== "file:") {
    try {
      const result = await loadStaticHolidayData(year);
      if (!result.items.length) throw new Error("Static holiday JSON is empty");
      holidays = result.items;
      holidayDataMeta = result.meta || {};
      writeHolidayCache(year, holidays);
      loadedFrom = "github";
    } catch (error) {
      lastError = error;
    }
  }

  if (!['api', 'github'].includes(loadedFrom)) {
    const cached = readHolidayCache(year);
    holidays = cached.length ? cached : normalizeHolidays(OFFLINE_HOLIDAYS[year] || []);
    loadedFrom = cached.length ? "cache" : "offline";
  }

  if (lastError) console.info("Holiday online data unavailable; using a fallback.", lastError);
  holidayLoadedFrom = loadedFrom;
  renderHolidaySyncStatus(loadedFrom);
  renderHolidayTable();
  renderNextHoliday();
  renderNotifications();
}


function loadNotificationReadIds() {
  const value = parseStoredJson(STORAGE.notificationReads, STORAGE.notificationReads, []);
  return new Set(Array.isArray(value) ? value.map(String) : []);
}

function saveNotificationReadIds(ids) {
  localStorage.setItem(STORAGE.notificationReads, JSON.stringify(Array.from(ids)));
}

function getHolidayNotifications() {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return holidays
    .map(item => {
      const date = parseIsoDate(holidayDate(item));
      if (!date) return null;
      date.setHours(0, 0, 0, 0);
      const days = Math.round((date.getTime() - today.getTime()) / 86400000);
      if (days < 0 || days > HOLIDAY_NOTIFICATION_WINDOW_DAYS) return null;
      const name = displayHolidayName(item);
      const formattedDate = date.toLocaleDateString(gregorianLocale(), { year: "numeric", month: "long", day: "numeric", weekday: "short" }) + buddhistYearSuffix(date);
      let message;
      if (days === 0) message = t("holiday_today", { name });
      else if (days === 1) message = t("holiday_tomorrow", { name });
      else if (days <= 7) message = t("holiday_in_days", { name, days });
      else message = t("holiday_on_date", { name, date: formattedDate });
      return {
        id: `holiday:${holidayDate(item)}`,
        date,
        days,
        name,
        message,
        formattedDate,
        companyConfirmed: Boolean(item.company_confirmed)
      };
    })
    .filter(Boolean)
    .sort((a, b) => a.date - b.date)
    .slice(0, HOLIDAY_NOTIFICATION_LIMIT);
}

function unreadNotificationCount() {
  const readIds = loadNotificationReadIds();
  return getHolidayNotifications().filter(item => !readIds.has(item.id)).length;
}

function renderNotificationNavBadge() {
  if (!current || !$("mainNav")) return;
  document.querySelectorAll("#mainNav button").forEach(button => {
    const item = NAV.find(entry => entry[0] === button.dataset.page);
    if (!item) return;
    button.replaceChildren(document.createTextNode(t(item[1])));
    if (button.dataset.page === "notifications") {
      const count = unreadNotificationCount();
      if (count > 0) {
        const badge = document.createElement("span");
        badge.className = "nav-count";
        badge.textContent = String(count);
        button.appendChild(badge);
      }
    }
  });
}

function markNotificationRead(id) {
  const readIds = loadNotificationReadIds();
  readIds.add(String(id));
  saveNotificationReadIds(readIds);
  renderNotifications();
}

function markAllNotificationsRead() {
  const readIds = loadNotificationReadIds();
  getHolidayNotifications().forEach(item => readIds.add(item.id));
  saveNotificationReadIds(readIds);
  renderNotifications();
}

function renderNotifications() {
  const list = $("notificationList");
  if (!list) return;
  const items = getHolidayNotifications();
  const readIds = loadNotificationReadIds();
  if (!items.length) {
    list.innerHTML = `<div class="empty-state">🔔<p>${escapeHtml(t("notifications_empty"))}</p></div>`;
  } else {
    list.innerHTML = items.map(item => {
      const isRead = readIds.has(item.id);
      const timing = item.days === 0 ? t("today") : item.days === 1 ? t("tomorrow") : t("days_remaining", { days: item.days });
      const confirmation = item.companyConfirmed ? t("company_holiday_confirmed") : t("holiday_company_note");
      return `<article class="notification-card ${isRead ? "read" : "unread"}">` +
        `<div class="notification-icon">📅</div>` +
        `<div class="notification-body"><div class="notification-title-row"><h4>${escapeHtml(t("holiday_notification_title"))}</h4>` +
        `<span class="badge ${isRead ? "approved" : "pending"}">${escapeHtml(t(isRead ? "notification_read" : "notification_unread"))}</span></div>` +
        `<p class="notification-message">${escapeHtml(item.message)}</p>` +
        `<div class="notification-meta"><span>${escapeHtml(item.formattedDate)}</span><span>${escapeHtml(timing)}</span><span>${escapeHtml(t("notification_generated"))}</span></div>` +
        `<small>${escapeHtml(confirmation)}</small>` +
        `${isRead ? "" : `<button class="soft notification-read" data-notification-read="${escapeHtml(item.id)}">${escapeHtml(t("mark_as_read"))}</button>`}</div></article>`;
    }).join("");
    list.querySelectorAll("[data-notification-read]").forEach(button => {
      button.onclick = () => markNotificationRead(button.dataset.notificationRead);
    });
  }
  if ($("notificationSummary")) {
    $("notificationSummary").textContent = t("notification_summary", {
      count: items.length,
      unread: items.filter(item => !readIds.has(item.id)).length,
      days: HOLIDAY_NOTIFICATION_WINDOW_DAYS
    });
  }
  if ($("markNotificationsRead")) $("markNotificationsRead").disabled = !items.length || items.every(item => readIds.has(item.id));
  renderNotificationNavBadge();
}

function renderHolidaySyncStatus(loadedFrom) {
  const element = $("holidaySyncStatus");
  if (!element) return;
  if (loadedFrom === "github") {
    const updated = holidayDataMeta.updated_at
      ? formatWithBuddhistYear(new Date(holidayDataMeta.updated_at))
      : "";
    const version = updated ? t("data_version", { value: updated }) : "";
    element.textContent = t("github_sync_status", { version });
    return;
  }
  if (location.protocol === "file:") {
    element.textContent = t("offline_status");
    return;
  }
  if (loadedFrom === "api") {
    void renderBackendSyncStatus(element);
    return;
  }
  element.textContent = loadedFrom === "cache" ? t("cache_status") : t("fallback_status");
}

async function renderBackendSyncStatus(element) {
  try {
    const response = await fetch(apiUrl("/api/holidays/sync-status"), { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const status = await response.json();
    if (!status.enabled) {
      element.textContent = t("auto_sync_disabled");
      return;
    }
    const last = status.last_finished_at
      ? t("last_sync", { value: formatWithBuddhistYear(new Date(status.last_finished_at)) })
      : "";
    element.textContent = t("api_sync_status", { time: status.daily_time, last });
  } catch (error) {
    console.info("Holiday sync status unavailable.", error);
    element.textContent = t("cache_status");
  }
}

function renderHolidayTable() {
  if (!$("holidayRows")) return;
  $("holidayRows").innerHTML = holidays.map(item =>
    `<tr><td>${escapeHtml(holidayDate(item))}</td>` +
    `<td>${escapeHtml(displayHolidayName(item))}</td>` +
    `<td>${escapeHtml(t("official_holiday"))}</td>` +
    `<td><span class="badge ${item.company_confirmed ? "approved" : "pending"}">${escapeHtml(reviewStatusText(item))}</span></td></tr>`
  ).join("") || `<tr><td colspan="4">${escapeHtml(t("no_data"))}</td></tr>`;
}

function renderNextHoliday() {
  if (!$("nextHolidayDate") || !$("nextHolidayName")) return;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const next = holidays.find(item => new Date(`${holidayDate(item)}T00:00:00`) >= today);
  if (!next) {
    $("nextHolidayDate").textContent = "—";
    $("nextHolidayName").textContent = t("no_data");
    return;
  }
  const date = new Date(`${holidayDate(next)}T00:00:00`);
  $("nextHolidayDate").textContent = date.toLocaleDateString(gregorianLocale(), { day: "2-digit", month: "short" }).toUpperCase();
  $("nextHolidayName").textContent = `${displayHolidayName(next)} · ${t("thailand")}`;
}

function renderCalendarWeekdays() {
  if (!$("calendarWeekdays")) return;
  const formatter = new Intl.DateTimeFormat(lang, { weekday: "short" });
  const sunday = new Date(2026, 0, 4);
  $("calendarWeekdays").innerHTML = Array.from({ length: 7 }, (_, index) => {
    const date = new Date(sunday);
    date.setDate(sunday.getDate() + index);
    return `<span>${escapeHtml(formatter.format(date))}</span>`;
  }).join("");
}

function renderCalendar() {
  if (!$("calendarGrid") || !$("calendarTitle")) return;
  const year = calendarCursor.getFullYear();
  const month = calendarCursor.getMonth();
  $("calendarTitle").textContent = calendarCursor.toLocaleDateString(gregorianLocale(), { year: "numeric", month: "long" }) + buddhistYearSuffix(calendarCursor);
  if ($("calendarNote")) {
    $("calendarNote").textContent = holidays.length ? "" : t("calendar_no_holiday_data");
    $("calendarNote").classList.toggle("hidden", holidays.length > 0);
  }
  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const previousMonthDays = new Date(year, month, 0).getDate();
  const holidayMap = new Map(holidays.map(item => [holidayDate(item), item]));
  const cells = [];
  for (let index = firstDay - 1; index >= 0; index -= 1) {
    cells.push({ number: previousMonthDays - index, muted: true });
  }
  for (let day = 1; day <= daysInMonth; day += 1) {
    const date = new Date(year, month, day);
    const key = localIsoDate(date);
    const classification = current ? classifyDemoDate(date) : null;
    cells.push({ number: day, date, holiday: holidayMap.get(key), classification });
  }
  let next = 1;
  while (cells.length % 7) cells.push({ number: next++, muted: true });
  $("calendarGrid").innerHTML = cells.map(cell => {
    const category = cell.classification?.category || "";
    const className = category === "rotation_workday" || category === "override_workday"
      ? "rotation-work"
      : category === "rotation_day_off" || category === "override_day_off"
        ? "rotation-off"
        : category === "sunday" ? "sunday-off" : "";
    let note = "";
    if (cell.holiday) note = displayHolidayName(cell.holiday);
    else if (category === "rotation_workday") note = t("saturday_work_group", { group: cell.classification.workingGroup });
    else if (category === "rotation_day_off") note = t("personal_rotation_day_off");
    else if (category === "override_workday") note = cell.classification.note || t("special_workday");
    else if (category === "override_day_off") note = cell.classification.note || t("special_day_off");
    return `<div class="day ${cell.muted ? "muted" : ""} ${cell.holiday ? "holiday" : ""} ${className}">` +
      `<b>${cell.number}</b>${note ? `<small>${escapeHtml(note)}</small>` : ""}</div>`;
  }).join("");
  if ($("calendarRotationInfo") && current) {
    $("calendarRotationInfo").textContent = t("calendar_rotation_info", { group: currentRotationGroup() });
  }
}

async function ensureHolidayYearHasData(year) {
  if (holidays.length || !CONFIG.API_BASE_URL || !apiToken) return;
  if (current?.role !== "hr" && current?.role !== "admin") return;

  try {
    const response = await fetch(apiUrl(`/api/holidays/initialize/${year}`), {
      method: "POST",
      headers: { Authorization: `Bearer ${apiToken}` }
    });
    if (response.ok) {
      await loadHolidays(year);
    }
  } catch (error) {
    console.info(`Could not auto-initialize holiday data for ${year}.`, error);
  }
}

async function changeCalendarYear(offset) {
  calendarCursor.setDate(1);
  calendarCursor.setFullYear(calendarCursor.getFullYear() + offset);
  await loadHolidays(calendarCursor.getFullYear());
  await ensureHolidayYearHasData(calendarCursor.getFullYear());
  renderCalendar();
}

async function changeCalendarMonth(offset) {
  const previousYear = calendarCursor.getFullYear();
  calendarCursor.setDate(1);
  calendarCursor.setMonth(calendarCursor.getMonth() + offset);
  if (calendarCursor.getFullYear() !== previousYear) {
    await loadHolidays(calendarCursor.getFullYear());
    await ensureHolidayYearHasData(calendarCursor.getFullYear());
  }
  renderCalendar();
}

async function goToCurrentMonth() {
  const previousYear = calendarCursor.getFullYear();
  const today = new Date();
  calendarCursor.setFullYear(today.getFullYear(), today.getMonth(), 1);
  if (calendarCursor.getFullYear() !== previousYear) {
    await loadHolidays(calendarCursor.getFullYear());
  }
  renderCalendar();
}

async function syncHolidays() {
  if (!CONFIG.API_BASE_URL || !apiToken) {
    try {
      await loadHolidays(calendarCursor.getFullYear());
      renderCalendar();
      addAudit("holiday_sync_action");
      alert(t("holidays_reloaded"));
    } catch (error) {
      alert(t("sync_failed", { error: error.message }));
    }
    return;
  }
  try {
    const response = await fetch(apiUrl("/api/holidays/annual-rollover"), {
      method: "POST",
      headers: { Authorization: `Bearer ${apiToken}` }
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || `HTTP ${response.status}`);
    await loadHolidays(calendarCursor.getFullYear());
    renderCalendar();
    addAudit("holiday_sync_action");
    alert(data.errors?.length ? t("current_year_only") : t("backend_sync_success"));
  } catch (error) {
    alert(t("sync_failed", { error: error.message }));
  }
}

async function loadRotationFromBackend() {
  const headers = { Authorization: `Bearer ${apiToken}` };
  const [settingsResponse, overridesResponse] = await Promise.all([
    fetch(apiUrl("/api/schedules/settings"), { headers, cache: "no-store" }),
    fetch(apiUrl(`/api/schedules/overrides?year=${calendarCursor.getFullYear()}`), { headers, cache: "no-store" })
  ]);
  if (settingsResponse.ok) rotationSettings = normalizeRotationSettings(await settingsResponse.json());
  if (overridesResponse.ok) rotationOverrides = (await overridesResponse.json()).map(normalizeOverride);
  saveRotationState();
  renderRotationPage();
  renderCalendar();
  updateLeaveCalculation();
}

function upcomingSaturdayRows(count = 12) {
  const rows = [];
  const date = new Date();
  while (date.getDay() !== 6) date.setDate(date.getDate() + 1);
  for (let index = 0; index < count; index += 1) {
    const result = classifyDemoDate(date);
    rows.push({ ...result, date: new Date(date) });
    date.setDate(date.getDate() + 7);
  }
  return rows;
}

function renderRotationPage() {
  if (!$("rotationRows") || !current) return;
  $("rotationMyGroup").textContent = t("rotation_group_value", { group: currentRotationGroup() });
  $("rotationAnchor").value = rotationSettings.anchorDate;
  $("rotationFirstGroup").value = rotationSettings.firstWorkingGroup;
  $("rotationSaturdayEnabled").checked = Boolean(rotationSettings.saturdayEnabled);
  const canEdit = ["hr", "admin"].includes(current.role);
  ["rotationAnchor", "rotationFirstGroup", "rotationSaturdayEnabled", "saveRotation", "rotationOverrideDate", "rotationOverrideType", "rotationOverrideGroup", "rotationOverrideNote", "addRotationOverride"].forEach(id => {
    if ($(id)) $(id).disabled = !canEdit;
  });
  $("rotationRows").innerHTML = upcomingSaturdayRows().map(item =>
    `<tr><td>${escapeHtml(formatWithBuddhistYear(item.date, { dateOnly: true }))}</td>` +
    `<td>${escapeHtml(item.workingGroup || "—")}</td>` +
    `<td><span class="badge ${item.isWorkday ? "approved" : "pending"}">${escapeHtml(t(item.isWorkday ? "scheduled_workday" : "scheduled_day_off"))}</span></td>` +
    `<td>${escapeHtml(item.note || t(item.category))}</td></tr>`
  ).join("");
  $("rotationOverrideRows").innerHTML = rotationOverrides.map(item =>
    `<tr><td>${escapeHtml(item.date)}</td><td>${escapeHtml(t(item.overrideType === "WORKDAY" ? "special_workday" : "special_day_off"))}</td>` +
    `<td>${escapeHtml(item.rotationGroup)}</td><td>${escapeHtml(item.note || "—")}</td>` +
    `<td>${canEdit ? `<button class="ghost" onclick="removeRotationOverride('${escapeHtml(item.id)}')">${escapeHtml(t("delete"))}</button>` : ""}</td></tr>`
  ).join("") || `<tr><td colspan="5">${escapeHtml(t("no_data"))}</td></tr>`;
}

async function saveRotationSettings() {
  if (!current || !["hr", "admin"].includes(current.role)) return;
  const anchorDate = $("rotationAnchor").value;
  const anchor = parseIsoDate(anchorDate);
  if (!anchor || anchor.getDay() !== 6) {
    $("rotationMessage").textContent = t("anchor_must_be_saturday");
    return;
  }
  rotationSettings = {
    ...rotationSettings,
    anchorDate,
    firstWorkingGroup: $("rotationFirstGroup").value,
    saturdayEnabled: $("rotationSaturdayEnabled").checked
  };
  if (CONFIG.API_BASE_URL && apiToken) {
    const response = await fetch(apiUrl("/api/schedules/settings"), {
      method: "PUT",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${apiToken}` },
      body: JSON.stringify({
        name: rotationSettings.name,
        anchor_date: rotationSettings.anchorDate,
        first_working_group: rotationSettings.firstWorkingGroup,
        cycle_weeks: 2,
        saturday_enabled: rotationSettings.saturdayEnabled,
        sunday_is_day_off: rotationSettings.sundayIsDayOff
      })
    });
    if (!response.ok) {
      $("rotationMessage").textContent = t("save_failed");
      return;
    }
    rotationSettings = normalizeRotationSettings(await response.json());
  }
  saveRotationState();
  $("rotationMessage").textContent = t("rotation_saved");
  renderRotationPage();
  renderCalendar();
  updateLeaveCalculation();
}

async function addRotationOverride() {
  if (!current || !["hr", "admin"].includes(current.role)) return;
  const item = normalizeOverride({
    id: Date.now(),
    date: $("rotationOverrideDate").value,
    overrideType: $("rotationOverrideType").value,
    rotationGroup: $("rotationOverrideGroup").value,
    note: $("rotationOverrideNote").value.trim()
  });
  if (!item.date) return;
  if (CONFIG.API_BASE_URL && apiToken) {
    const response = await fetch(apiUrl("/api/schedules/overrides"), {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${apiToken}` },
      body: JSON.stringify({ date: item.date, override_type: item.overrideType, rotation_group: item.rotationGroup, note: item.note })
    });
    if (!response.ok) return;
    Object.assign(item, normalizeOverride(await response.json()));
  }
  rotationOverrides = rotationOverrides.filter(existing => !(existing.date === item.date && existing.rotationGroup === item.rotationGroup));
  rotationOverrides.push(item);
  rotationOverrides.sort((a, b) => a.date.localeCompare(b.date));
  saveRotationState();
  renderRotationPage();
  renderCalendar();
  updateLeaveCalculation();
}

window.removeRotationOverride = async id => {
  const item = rotationOverrides.find(entry => String(entry.id) === String(id));
  if (!item) return;
  if (CONFIG.API_BASE_URL && apiToken && Number.isFinite(Number(item.id))) {
    const response = await fetch(apiUrl(`/api/schedules/overrides/${item.id}`), {
      method: "DELETE", headers: { Authorization: `Bearer ${apiToken}` }
    });
    if (!response.ok && response.status !== 404) return;
  }
  rotationOverrides = rotationOverrides.filter(entry => String(entry.id) !== String(id));
  saveRotationState();
  renderRotationPage();
  renderCalendar();
  updateLeaveCalculation();
};

function escapeHtml(value) {
  const element = document.createElement("div");
  element.textContent = String(value ?? "");
  return element.innerHTML;
}

function updateAIStatus() {
  if (!$("aiStatus")) return;
  const connected = Boolean(CONFIG.API_BASE_URL && apiToken);
  $("aiStatus").textContent = connected ? t("ai_online") : t("ai_offline");
  if ($("aiNote")) $("aiNote").textContent = connected ? t("ai_online_notice") : t("ai_demo_notice");
}

function renderSources(container, sources = []) {
  if (!Array.isArray(sources) || !sources.length) return;
  const wrapper = document.createElement("div");
  wrapper.className = "source-list";
  wrapper.setAttribute("aria-label", t("ai_sources"));
  sources.slice(0, 4).forEach(source => {
    const chip = document.createElement("span");
    chip.className = "source-chip";
    const title = source.title || source.source || t("ai_sources");
    const score = Number.isFinite(Number(source.score)) ? ` · ${Math.round(Number(source.score) * 100)}%` : "";
    chip.textContent = `${title}${score}`;
    chip.title = source.source || title;
    wrapper.appendChild(chip);
  });
  container.appendChild(wrapper);
}

function addChatBubble(message, pending = false) {
  const bubble = document.createElement("div");
  bubble.className = `bubble ${message.role === "user" ? "user" : "bot"}${pending ? " pending" : ""}`;
  bubble.textContent = message.content;
  if (message.role === "assistant") renderSources(bubble, message.sources);
  $("aiMessages").appendChild(bubble);
  $("aiChat").scrollTop = $("aiChat").scrollHeight;
  return bubble;
}

function renderAIConversation() {
  if (!$("aiMessages")) return;
  $("aiMessages").replaceChildren();
  if (!aiHistory.length) {
    addChatBubble({ role: "assistant", content: t("ai_welcome"), sources: [] });
    return;
  }
  aiHistory.forEach(item => addChatBubble(item));
}

function clearAIChat() {
  aiHistory = [];
  saveAIHistory();
  renderAIConversation();
  $("aiInput").focus();
}

function detectChatLanguage(text, fallback = lang) {
  const value = String(text || "").trim();
  if (/[\u0E00-\u0E7F]/.test(value)) return "th";
  if (/[\u3400-\u9FFF]/.test(value)) return "zh-TW";
  if (/[A-Za-z]/.test(value)) return "en";
  return SUPPORTED_LANGUAGES.includes(fallback) ? fallback : "zh-TW";
}

function demoChatReply(query) {
  const normalized = query.toLowerCase().trim();
  const replyLang = detectChatLanguage(query, lang);
  const includesAny = words => words.some(word => normalized.includes(word.toLowerCase()));
  const plain = normalized.replace(/[!?？！，。,.]/g, "").trim();
  const greetingWords = ["你好", "您好", "哈囉", "哈啰", "嗨", "hello", "hi", "hey", "สวัสดี", "หวัดดี"];

  if (greetingWords.some(word => plain === word || plain.startsWith(`${word} `))) {
    if (replyLang === "en") {
      return "Hello! I am the Emerald leave assistant. You can ask about leave policies, medical certificates, approval workflows, Thai holidays, Saturday rotations, or the current date and time.";
    }
    if (replyLang === "th") {
      return "สวัสดี ฉันคือผู้ช่วยการลาของ Emerald คุณสามารถถามเรื่องระเบียบการลา ใบรับรองแพทย์ ขั้นตอนอนุมัติ วันหยุดไทย ตารางเวรวันเสาร์ หรือวันและเวลาปัจจุบันได้";
    }
    return "你好！我是 Emerald 請假助理。你可以詢問請假規章、病假證明、審核流程、泰國假日、星期六輪休，以及目前日期或時間。";
  }

  const asksTime = includesAny([
    "現在幾點", "现在几点", "幾點了", "几点了", "現在時間", "现在时间",
    "what time is it", "current time", "time now",
    "ตอนนี้กี่โมง", "กี่โมงแล้ว", "เวลาเท่าไหร่"
  ]);
  const asksDate = includesAny([
    "今天幾號", "今天几号", "今天日期", "現在日期", "现在日期",
    "what date is it", "today's date", "current date",
    "วันนี้วันที่เท่าไหร่", "วันนี้วันอะไร"
  ]);
  if (asksTime || asksDate) {
    const now = new Date();
    const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone || "local time";
    const locale = replyLang === "zh-TW" ? "zh-TW" : replyLang;
    const dateText = new Intl.DateTimeFormat(locale, {
      year: "numeric", month: "2-digit", day: "2-digit", weekday: "long"
    }).format(now);
    const timeText = new Intl.DateTimeFormat(locale, {
      hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false
    }).format(now);
    if (replyLang === "en") {
      if (asksTime && asksDate) return `It is ${timeText} on ${dateText} (${timezone}).`;
      if (asksDate) return `Today is ${dateText} (${timezone}).`;
      return `The current time is ${timeText} (${timezone}).`;
    }
    if (replyLang === "th") {
      if (asksTime && asksDate) return `ขณะนี้เวลา ${timeText} น. วันที่ ${dateText} (${timezone})`;
      if (asksDate) return `วันนี้คือ ${dateText} (${timezone})`;
      return `ขณะนี้เวลา ${timeText} น. (${timezone})`;
    }
    if (asksTime && asksDate) return `現在是 ${dateText} ${timeText}（${timezone}）。`;
    if (asksDate) return `今天是 ${dateText}（${timezone}）。`;
    return `現在時間是 ${timeText}（${timezone}）。`;
  }

  if (includesAny(["特休餘額", "年假餘額", "還有幾天特休", "还有几天特休", "剩幾天特休", "leave balance", "annual leave balance", "days of annual leave", "วันลาพักร้อนคงเหลือ", "เหลือวันลา"])) {
    if (replyLang === "en") return "Based on the demo account, you have 12 annual leave days remaining. Connect the backend to show each employee's real-time balance.";
    if (replyLang === "th") return "ตามบัญชีสาธิต คุณมีวันลาพักร้อนคงเหลือ 12 วัน เมื่อเชื่อมต่อระบบหลังบ้านแล้วจะแสดงยอดคงเหลือจริงของพนักงานแต่ละคน";
    return "依目前示範帳號，你還有 12 天特休。連接正式後端後，會顯示每位員工的即時餘額。";
  }

  if (includesAny(["公司介紹", "公司資料", "emerald nonwovens", "company profile", "about emerald", "ข้อมูลบริษัท", "เกี่ยวกับบริษัท"])) {
    if (replyLang === "en") return "Emerald Nonwovens International Co., Ltd. is publicly listed at Khao Yoi, Phetchaburi, Thailand and supplies disposable protective apparel, surgical gowns, drapes, and other medical nonwoven products. The website lists public operating hours of Monday–Saturday, 08:00–17:00 (GMT+7); this is not a confirmed employee shift schedule.";
    if (replyLang === "th") return "Emerald Nonwovens International Co., Ltd. ตั้งอยู่ที่อำเภอเขาย้อย จังหวัดเพชรบุรี และผลิตชุดป้องกันใช้ครั้งเดียว เสื้อกาวน์และผ้าคลุมผ่าตัด รวมถึงผลิตภัณฑ์นอนวูฟเวนทางการแพทย์ เว็บไซต์ระบุเวลาทำการวันจันทร์–เสาร์ 08:00–17:00 น. (GMT+7) ซึ่งไม่ใช่การยืนยันกะงานของพนักงานแต่ละคน";
    return "Emerald Nonwovens International Co., Ltd. 的公開地址位於泰國佛丕府考艾縣，產品包含一次性防護服、手術衣、手術鋪單與其他醫療用不織布產品。官網列出的公開營業時間為週一至週六 08:00–17:00（GMT+7），但這不等於每位員工的正式班別。";
  }

  if (includesAny(["新人", "報到", "规章", "規章", "秩序", "onboarding", "new employee", "work rules", "employee handbook", "พนักงานใหม่", "ปฐมนิเทศ", "ระเบียบ"])) {
    if (replyLang === "en") return "Open the New employee hub and complete the checklist for attendance, Saturday rotation, leave, safety/PPE, hygiene/quality, confidentiality, emergencies, and contacts. The displayed rules are templates until HR uploads and confirms the official handbook; I should not invent missing company policy.";
    if (replyLang === "th") return "เปิดศูนย์พนักงานใหม่และทำรายการเรื่องเวลาเข้างาน เวรวันเสาร์ การลา ความปลอดภัย/PPE สุขอนามัย/คุณภาพ ความลับ เหตุฉุกเฉิน และผู้ติดต่อ เนื้อหาที่แสดงเป็นแม่แบบจนกว่า HR จะอัปโหลดและยืนยันคู่มือฉบับจริง ฉันไม่ควรแต่งระเบียบบริษัทที่ไม่มีข้อมูล";
    return "請先到「新人專區」完成出勤打卡、星期六輪班、請假、安全／PPE、衛生品質、保密拍照、緊急事件與聯絡人清單。頁面中的規則目前是待 HR 確認的範本；HR 尚未上傳正式員工手冊前，Chatbot 不應自行編造公司規章。";
  }

  if (includesAny(["病假", "醫療", "medical", "certificate", "sick", "ลาป่วย", "ใบรับรองแพทย์"])) {
    return replyLang === "en"
      ? "For the demo policy, a medical certificate may be requested for extended sick leave. The final requirement should follow your company's HR policy."
      : replyLang === "th"
        ? "ตามนโยบายตัวอย่าง อาจต้องใช้ใบรับรองแพทย์เมื่อลาป่วยหลายวัน โปรดยึดระเบียบของฝ่ายบุคคลบริษัทเป็นหลัก"
        : "依示範規章，連續多日病假可能需要醫療證明；實際門檻仍以公司 HR 規章為準。";
  }
  if (includesAny(["審核", "主管", "hr", "approve", "approval", "อนุมัติ", "หัวหน้า"])) {
    return replyLang === "en"
      ? "A leave request normally goes to the direct manager first, then HR for final confirmation. A returned request should include a reason."
      : replyLang === "th"
        ? "โดยทั่วไปคำขอลาจะส่งให้หัวหน้างานอนุมัติก่อน แล้วฝ่ายบุคคลยืนยันขั้นสุดท้าย หากส่งกลับควรระบุเหตุผล"
        : "一般流程是先由直屬主管審核，再交 HR 最終確認；若退回，應附上原因。";
  }
  if (includesAny(["輪休", "星期六", "週六", "周六", "saturday", "rotation", "วันเสาร์", "ตารางเวร"])) {
    const date = new Date();
    while (date.getDay() !== 6) date.setDate(date.getDate() + 1);
    if (includesAny(["下週", "下周", "next saturday", "เสาร์หน้า"])) date.setDate(date.getDate() + 7);
    const result = classifyDemoDate(date);
    const dateText = date.toLocaleDateString(replyLang === "th" ? "th-TH-u-ca-gregory" : replyLang) + (replyLang === "th" ? ` (พ.ศ. ${date.getFullYear() + 543})` : "");
    return replyLang === "en"
      ? `${dateText}: your group is ${currentRotationGroup()}, and the working group is ${result.workingGroup || "—"}. You ${result.isWorkday ? "are scheduled to work" : "are off under the rotation schedule"}.`
      : replyLang === "th"
        ? `${dateText}: กลุ่มของคุณคือ ${currentRotationGroup()} และกลุ่มที่ทำงานคือ ${result.workingGroup || "—"} ดังนั้นคุณ${result.isWorkday ? "ต้องมาทำงาน" : "เป็นวันหยุดตามรอบเวร"}`
        : `${dateText}：你是 ${currentRotationGroup()} 組，當天上班組別為 ${result.workingGroup || "—"} 組，因此你${result.isWorkday ? "需要上班" : "輪休，不需要上班"}。`;
  }
  if (includesAny(["泰國", "假日", "holiday", "thailand", "วันหยุด", "ไทย"])) {
    return replyLang === "en"
      ? "The GitHub Actions workflow checks Thai holidays every day at about 06:30 Bangkok time and redeploys Pages when data changes."
      : replyLang === "th"
        ? "GitHub Actions จะตรวจสอบวันหยุดไทยทุกวันประมาณ 06:30 น. ตามเวลากรุงเทพฯ และเผยแพร่ Pages ใหม่เมื่อข้อมูลเปลี่ยนแปลง"
        : "GitHub Actions 會每天約泰國時間 06:30 檢查假日；資料有變更時會更新 JSON 並重新部署 Pages。";
  }

  if (replyLang === "en") return "I am not sure which item you want to check. Try asking about new-employee rules, the company profile, sick-leave certificates, approval steps, Thai holidays, Saturday rotations, leave balance, or the current date and time.";
  if (replyLang === "th") return "ฉันยังไม่แน่ใจว่าคุณต้องการตรวจสอบเรื่องใด ลองถามเรื่องระเบียบพนักงานใหม่ ข้อมูลบริษัท ใบรับรองการลาป่วย ขั้นตอนอนุมัติ วันหยุดไทย ตารางเวรวันเสาร์ ยอดวันลาคงเหลือ หรือวันและเวลาปัจจุบัน";
  return "我還不確定你想查哪一項。可以詢問新人規章、公司介紹、病假證明、審核流程、泰國假日、星期六輪休、特休餘額，或目前日期與時間。";
}

async function sendAI() {
  const input = $("aiInput");
  const query = input.value.trim();
  if (!query || $("aiSend").disabled) return;

  const userMessage = { role: "user", content: query, sources: [] };
  aiHistory.push(userMessage);
  saveAIHistory();
  addChatBubble(userMessage);
  input.value = "";
  addAudit("ai_query_action");

  $("aiSend").disabled = true;
  const pendingBubble = addChatBubble({ role: "assistant", content: t("ai_searching"), sources: [] }, true);

  try {
    let answer;
    let sources = [];
    if (!CONFIG.API_BASE_URL || !apiToken) {
      await new Promise(resolve => setTimeout(resolve, 350));
      answer = demoChatReply(query);
    } else {
      const messageLanguage = detectChatLanguage(query, lang);
      const response = await fetch(apiUrl("/api/rag/chat"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${apiToken}`
        },
        body: JSON.stringify({
          message: query,
          history: aiHistory.slice(0, -1).slice(-8).map(item => ({ role: item.role, content: item.content })),
          top_k: 3,
          language: messageLanguage
        })
      });
      const data = await response.json();
      if (response.status === 429) throw new Error("RATE_LIMITED");
      if (!response.ok) throw new Error(data.detail || `HTTP ${response.status}`);
      answer = data.answer || t("ai_no_results");
      sources = Array.isArray(data.sources) ? data.sources : [];
    }

    pendingBubble.remove();
    const assistantMessage = { role: "assistant", content: answer, sources };
    aiHistory.push(assistantMessage);
    saveAIHistory();
    addChatBubble(assistantMessage);
  } catch (error) {
    console.info("RAG chat unavailable.", error);
    pendingBubble.remove();
    const content = error.message === "RATE_LIMITED"
      ? t("ai_rate_limited")
      : `${t("ai_error")} ${t("backend_unavailable")}`;
    const assistantMessage = { role: "assistant", content, sources: [] };
    aiHistory.push(assistantMessage);
    saveAIHistory();
    addChatBubble(assistantMessage);
  } finally {
    $("aiSend").disabled = false;
    input.focus();
  }
}

boot().catch(error => {
  console.error(error);
  document.body.innerHTML = `<pre>${escapeHtml(t("app_start_failed"))}</pre>`;
});
