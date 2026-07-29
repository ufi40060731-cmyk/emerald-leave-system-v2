/*
 * Full-stack same-origin deployment.
 *
 * Railway serves this frontend and FastAPI from the same HTTPS domain.
 * The browser calls /api on the same origin; MySQL remains private behind FastAPI.
 *
 * When opened directly from disk (file://), demo mode is used as a safe fallback.
 */
(() => {
  "use strict";
  const hosted = location.protocol === "https:" || location.protocol === "http:";

  window.EMERALD_CONFIG = Object.freeze({
    APP_MODE: hosted ? "production" : "demo",
    API_BASE_URL: hosted ? location.origin : "",
    AUTO_CONNECT_LOCALHOST: true
  });
})();
