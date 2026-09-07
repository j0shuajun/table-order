// Shared API client: token storage (localStorage), fetch wrapper, formatting.
// Exposes a global `API` used by both the customer and admin apps.
(function () {
  "use strict";

  var STORE_ID = "store001"; // single-store MVP
  var ADMIN_TOKEN_KEY = "to_admin_token";
  var TABLE_TOKEN_KEY = "to_table_token";
  var TABLE_INFO_KEY = "to_table_info"; // {store_id, table_number} for auto re-auth

  function getAdminToken() {
    return localStorage.getItem(ADMIN_TOKEN_KEY);
  }
  function setAdminToken(t) {
    if (t) localStorage.setItem(ADMIN_TOKEN_KEY, t);
    else localStorage.removeItem(ADMIN_TOKEN_KEY);
  }
  function getTableToken() {
    return localStorage.getItem(TABLE_TOKEN_KEY);
  }
  function setTableToken(t) {
    if (t) localStorage.setItem(TABLE_TOKEN_KEY, t);
    else localStorage.removeItem(TABLE_TOKEN_KEY);
  }
  function getTableInfo() {
    try {
      return JSON.parse(localStorage.getItem(TABLE_INFO_KEY) || "null");
    } catch (e) {
      return null;
    }
  }
  function setTableInfo(info) {
    if (info) localStorage.setItem(TABLE_INFO_KEY, JSON.stringify(info));
    else localStorage.removeItem(TABLE_INFO_KEY);
  }

  // Thrown by request() on non-2xx so callers can branch on status.
  function ApiError(status, detail) {
    this.status = status;
    this.detail = detail || "요청을 처리하지 못했습니다.";
    this.message = this.detail;
  }
  ApiError.prototype = Object.create(Error.prototype);

  async function request(path, options) {
    options = options || {};
    var headers = { "Content-Type": "application/json" };
    if (options.token) headers["Authorization"] = "Bearer " + options.token;
    var res = await fetch(path, {
      method: options.method || "GET",
      headers: headers,
      body: options.body ? JSON.stringify(options.body) : undefined,
    });
    var data = null;
    var text = await res.text();
    if (text) {
      try {
        data = JSON.parse(text);
      } catch (e) {
        data = null;
      }
    }
    if (!res.ok) {
      var detail = data && data.detail ? data.detail : "요청 실패 (" + res.status + ")";
      throw new ApiError(res.status, detail);
    }
    return data;
  }

  function formatWon(n) {
    return (n || 0).toLocaleString("ko-KR") + "원";
  }

  // ISO 8601 UTC (…Z) -> local HH:MM (KST in browser).
  function formatTime(iso) {
    if (!iso) return "";
    var d = new Date(iso);
    return d.toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" });
  }
  function formatDateTime(iso) {
    if (!iso) return "";
    var d = new Date(iso);
    return d.toLocaleString("ko-KR", {
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  window.API = {
    STORE_ID: STORE_ID,
    request: request,
    ApiError: ApiError,
    getAdminToken: getAdminToken,
    setAdminToken: setAdminToken,
    getTableToken: getTableToken,
    setTableToken: setTableToken,
    getTableInfo: getTableInfo,
    setTableInfo: setTableInfo,
    formatWon: formatWon,
    formatTime: formatTime,
    formatDateTime: formatDateTime,
  };
})();
