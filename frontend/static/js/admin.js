// Admin app: login, dashboard grid, realtime SSE, order detail/status/delete,
// table management, and menu CRUD.
(function () {
  "use strict";
  var A = window.API;

  var STATUS_LABEL = { pending: "접수", preparing: "준비중", completed: "완료" };
  var STATUS_FLOW = ["pending", "preparing", "completed"];

  var state = {
    token: null,
    tables: [],
    categories: [],
    source: null, // EventSource
    newTables: {}, // table_id -> timeout id (highlight)
    openTableId: null, // table whose detail modal is open
  };

  function $(id) {
    return document.getElementById(id);
  }
  function toast(msg) {
    var t = $("toast");
    t.textContent = msg;
    t.classList.add("show");
    setTimeout(function () {
      t.classList.remove("show");
    }, 2200);
  }
  function escapeHtml(s) {
    return (s || "").replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function statusBadge(status) {
    return "<span class='badge " + status + "'>" + (STATUS_LABEL[status] || status) + "</span>";
  }

  // --- auth ---------------------------------------------------------
  function showLogin(message) {
    $("admin-view").classList.add("hidden");
    $("login-view").classList.remove("hidden");
    $("login-error").textContent = message || "";
  }
  function showAdmin() {
    $("login-view").classList.add("hidden");
    $("admin-view").classList.remove("hidden");
  }

  async function boot() {
    state.token = A.getAdminToken();
    if (!state.token) {
      showLogin();
      return;
    }
    try {
      await loadDashboard();
      showAdmin();
      connectStream();
    } catch (e) {
      if (e.status === 401) {
        A.setAdminToken(null);
        showLogin("세션이 만료되었습니다. 다시 로그인해 주세요.");
      } else {
        showLogin(e.detail || "대시보드를 불러오지 못했습니다.");
      }
    }
  }

  async function login() {
    try {
      var res = await A.request("/api/admin/login", {
        method: "POST",
        body: {
          store_id: $("login-store").value.trim(),
          username: $("login-user").value.trim(),
          password: $("login-pw").value,
        },
      });
      state.token = res.token;
      A.setAdminToken(res.token);
      showAdmin();
      await loadDashboard();
      connectStream();
    } catch (e) {
      $("login-error").textContent = e.detail || "로그인에 실패했습니다.";
    }
  }

  function logout() {
    if (state.source) state.source.close();
    A.setAdminToken(null);
    state.token = null;
    showLogin();
  }

  // --- realtime -----------------------------------------------------
  function connectStream() {
    if (state.source) state.source.close();
    var src = new EventSource("/api/admin/stream?token=" + encodeURIComponent(state.token));
    state.source = src;
    src.onopen = function () {
      $("conn").textContent = "실시간 연결됨";
      $("conn").className = "badge completed";
    };
    src.onerror = function () {
      $("conn").textContent = "재연결 중…";
      $("conn").className = "badge preparing";
    };
    src.addEventListener("order_created", function (ev) {
      var data = JSON.parse(ev.data);
      highlightTable(data.table_id);
      refreshAfterEvent();
      toast("신규 주문 · 테이블 " + tableNumber(data.table_id));
    });
    ["order_updated", "order_deleted", "session_closed"].forEach(function (name) {
      src.addEventListener(name, function () {
        refreshAfterEvent();
      });
    });
  }

  function tableNumber(tableId) {
    var t = state.tables.filter(function (x) {
      return x.table_id === tableId;
    })[0];
    return t ? t.table_number : tableId;
  }

  function highlightTable(tableId) {
    if (state.newTables[tableId]) clearTimeout(state.newTables[tableId]);
    state.newTables[tableId] = setTimeout(function () {
      delete state.newTables[tableId];
      renderDashboard();
    }, 30000); // 신규 강조 ~30초
  }

  async function refreshAfterEvent() {
    await loadDashboard();
    if (state.openTableId != null) openTableDetail(state.openTableId, true);
  }

  // --- dashboard ----------------------------------------------------
  async function loadDashboard() {
    var data = await A.request("/api/admin/tables", { token: state.token });
    state.tables = data.tables || [];
    renderDashboard();
  }

  function renderDashboard() {
    var grid = $("tables-grid");
    grid.innerHTML = "";
    state.tables.forEach(function (t) {
      var card = document.createElement("div");
      card.className = "card table-card" + (state.newTables[t.table_id] ? " is-new" : "");
      card.onclick = function () {
        openTableDetail(t.table_id);
      };
      var head = document.createElement("div");
      head.className = "row space";
      head.innerHTML =
        "<strong>" +
        escapeHtml(t.table_number) +
        "</strong>" +
        (t.session_status === "active"
          ? "<span class='badge preparing'>이용 중</span>"
          : "<span class='badge'>비어 있음</span>");
      card.appendChild(head);
      var total = document.createElement("div");
      total.style.margin = "0.4rem 0";
      total.innerHTML =
        "<span class='muted'>현재 합계</span> <strong>" +
        A.formatWon(t.current_total) +
        "</strong> · 주문 " +
        t.order_count +
        "건";
      card.appendChild(total);
      (t.latest_orders || []).forEach(function (o) {
        var row = document.createElement("div");
        row.className = "order-item-row";
        row.innerHTML =
          "<span class='muted'>" +
          A.formatTime(o.created_at) +
          " · " +
          o.order_number.slice(-4) +
          "</span>" +
          statusBadge(o.status);
        card.appendChild(row);
      });
      grid.appendChild(card);
    });
    if (state.tables.length === 0) {
      grid.innerHTML = '<p class="muted">등록된 테이블이 없습니다.</p>';
    }
  }

  // --- order detail modal ------------------------------------------
  function openModal(title) {
    $("modal-title").textContent = title;
    $("modal-backdrop").classList.remove("hidden");
  }
  function closeModal() {
    $("modal-backdrop").classList.add("hidden");
    state.openTableId = null;
  }

  async function openTableDetail(tableId, keepOpen) {
    state.openTableId = tableId;
    if (!keepOpen) openModal("테이블 " + tableNumber(tableId) + " · 주문 상세");
    try {
      var data = await A.request("/api/admin/tables/" + tableId + "/orders", {
        token: state.token,
      });
      renderTableDetail(data);
    } catch (e) {
      $("modal-body").innerHTML = '<p class="muted">' + (e.detail || "불러오기 실패") + "</p>";
    }
  }

  function renderTableDetail(data) {
    var body = $("modal-body");
    body.innerHTML = "";
    var head = document.createElement("div");
    head.className = "row space";
    head.innerHTML =
      "<span class='muted'>세션 합계</span><strong>" + A.formatWon(data.session_total) + "</strong>";
    body.appendChild(head);
    if (!data.orders || data.orders.length === 0) {
      body.innerHTML += '<p class="muted">진행 중인 주문이 없습니다.</p>';
      addHistoryButton(body, data.table_id);
      return;
    }
    data.orders.forEach(function (o) {
      body.appendChild(orderBlock(o, data.table_id));
    });
    addHistoryButton(body, data.table_id);
  }

  function orderBlock(o, tableId) {
    var card = document.createElement("div");
    card.className = "card";
    card.style.margin = "0.6rem 0";
    var head = document.createElement("div");
    head.className = "row space";
    head.innerHTML =
      "<div><strong>" +
      o.order_number +
      "</strong> <span class='muted'>" +
      A.formatTime(o.created_at) +
      "</span></div>" +
      statusBadge(o.status);
    card.appendChild(head);
    o.items.forEach(function (it) {
      var row = document.createElement("div");
      row.className = "order-item-row";
      row.innerHTML =
        "<span>" + escapeHtml(it.menu_name) + " × " + it.quantity + "</span><span>" + A.formatWon(it.line_total) + "</span>";
      card.appendChild(row);
    });
    var actions = document.createElement("div");
    actions.className = "row";
    actions.style.marginTop = "0.5rem";
    STATUS_FLOW.forEach(function (s) {
      if (s === o.status) return;
      var b = document.createElement("button");
      b.className = "secondary";
      b.textContent = STATUS_LABEL[s] + "로";
      b.onclick = function () {
        changeStatus(o.order_id, s);
      };
      actions.appendChild(b);
    });
    var del = document.createElement("button");
    del.textContent = "삭제";
    del.onclick = function () {
      deleteOrder(o.order_id);
    };
    actions.appendChild(del);
    card.appendChild(actions);
    return card;
  }

  function addHistoryButton(body, tableId) {
    var wrap = document.createElement("div");
    wrap.className = "row";
    wrap.style.marginTop = "0.8rem";
    var complete = document.createElement("button");
    complete.textContent = "이용 완료";
    complete.onclick = function () {
      completeSession(tableId);
    };
    var hist = document.createElement("button");
    hist.className = "secondary";
    hist.textContent = "과거 내역";
    hist.onclick = function () {
      openHistory(tableId);
    };
    wrap.appendChild(complete);
    wrap.appendChild(hist);
    body.appendChild(wrap);
  }

  async function changeStatus(orderId, status) {
    try {
      await A.request("/api/admin/orders/" + orderId + "/status", {
        method: "POST",
        token: state.token,
        body: { status: status },
      });
      // SSE will refresh; refresh immediately too for responsiveness.
      refreshAfterEvent();
    } catch (e) {
      toast(e.detail || "상태 변경 실패");
    }
  }

  async function deleteOrder(orderId) {
    if (!window.confirm("이 주문을 삭제할까요?")) return;
    try {
      await A.request("/api/admin/orders/" + orderId, {
        method: "DELETE",
        token: state.token,
      });
      refreshAfterEvent();
      toast("주문을 삭제했습니다.");
    } catch (e) {
      toast(e.detail || "삭제 실패");
    }
  }

  async function completeSession(tableId) {
    if (!window.confirm("이 테이블 이용을 완료할까요? 현재 주문은 과거 내역으로 이동합니다.")) return;
    try {
      await A.request("/api/admin/tables/" + tableId + "/complete", {
        method: "POST",
        token: state.token,
      });
      toast("이용 완료 처리했습니다.");
      closeModal();
      loadDashboard();
    } catch (e) {
      toast(e.detail || "처리 실패");
    }
  }

  async function openHistory(tableId) {
    openModal("테이블 " + tableNumber(tableId) + " · 과거 내역");
    state.openTableId = null; // history is a snapshot, not live-refreshed
    try {
      var data = await A.request("/api/admin/tables/" + tableId + "/history", {
        token: state.token,
      });
      var body = $("modal-body");
      body.innerHTML = "";
      if (!data.sessions || data.sessions.length === 0) {
        body.innerHTML = '<p class="muted">과거 내역이 없습니다.</p>';
        return;
      }
      data.sessions.forEach(function (s) {
        var card = document.createElement("div");
        card.className = "card";
        card.style.margin = "0.6rem 0";
        card.innerHTML =
          "<div class='row space'><span class='muted'>" +
          A.formatDateTime(s.started_at) +
          " ~ " +
          A.formatDateTime(s.closed_at) +
          "</span><strong>" +
          A.formatWon(s.session_total) +
          "</strong></div>";
        s.orders.forEach(function (o) {
          var row = document.createElement("div");
          row.className = "order-item-row";
          row.innerHTML =
            "<span>" + o.order_number + " · " + o.items.length + "개 항목</span><span>" + A.formatWon(o.total_amount) + "</span>";
          card.appendChild(row);
        });
        body.appendChild(card);
      });
    } catch (e) {
      $("modal-body").innerHTML = '<p class="muted">' + (e.detail || "불러오기 실패") + "</p>";
    }
  }

  // --- table management --------------------------------------------
  async function loadTablesConfig() {
    try {
      var data = await A.request("/api/admin/tables/config", { token: state.token });
      var body = $("tables-config-body");
      body.innerHTML = "";
      (data.tables || []).forEach(function (t) {
        var tr = document.createElement("tr");
        tr.innerHTML =
          "<td>" + escapeHtml(t.table_number) + "</td><td class='muted'>" + A.formatDateTime(t.created_at) + "</td>";
        var actionCell = document.createElement("td");
        var reset = document.createElement("button");
        reset.className = "ghost";
        reset.textContent = "비밀번호 변경";
        reset.onclick = function () {
          resetTablePassword(t.table_id, t.table_number);
        };
        actionCell.appendChild(reset);
        tr.appendChild(actionCell);
        body.appendChild(tr);
      });
    } catch (e) {
      toast(e.detail || "테이블 목록 실패");
    }
  }

  async function createTable() {
    var number = $("new-table-number").value.trim();
    var pw = $("new-table-pw").value;
    if (!number || !pw) {
      toast("번호와 비밀번호를 입력하세요.");
      return;
    }
    try {
      await A.request("/api/admin/tables", {
        method: "POST",
        token: state.token,
        body: { table_number: number, password: pw },
      });
      $("new-table-number").value = "";
      $("new-table-pw").value = "";
      toast("테이블을 등록했습니다.");
      loadTablesConfig();
      loadDashboard();
    } catch (e) {
      toast(e.detail || "등록 실패");
    }
  }

  async function resetTablePassword(tableId, tableNumber) {
    var pw = window.prompt("테이블 " + tableNumber + "의 새 비밀번호", "");
    if (pw == null) return;
    if (!pw.trim()) {
      toast("비밀번호를 입력하세요.");
      return;
    }
    try {
      await A.request("/api/admin/tables/" + tableId + "/password", {
        method: "PUT",
        token: state.token,
        body: { password: pw },
      });
      toast("테이블 비밀번호를 변경했습니다.");
    } catch (e) {
      toast(e.detail || "변경 실패");
    }
  }

  // --- admin account -----------------------------------------------
  function openAdminPasswordChange() {
    openModal("관리자 비밀번호 변경");
    state.openTableId = null; // static form, not live-refreshed
    var body = $("modal-body");
    body.innerHTML =
      '<div class="grid">' +
      '<input id="apw-current" type="password" placeholder="현재 비밀번호" />' +
      '<input id="apw-new" type="password" placeholder="새 비밀번호" />' +
      '<button id="apw-submit">변경</button>' +
      '<div id="apw-error" class="muted"></div>' +
      "</div>";
    $("apw-submit").onclick = submitAdminPasswordChange;
  }

  async function submitAdminPasswordChange() {
    var current = $("apw-current").value;
    var next = $("apw-new").value;
    if (!current || !next.trim()) {
      $("apw-error").textContent = "현재 비밀번호와 새 비밀번호를 입력하세요.";
      return;
    }
    try {
      await A.request("/api/admin/password", {
        method: "POST",
        token: state.token,
        body: { current_password: current, new_password: next },
      });
      closeModal();
      toast("비밀번호를 변경했습니다.");
    } catch (e) {
      $("apw-error").textContent = e.detail || "변경 실패";
    }
  }

  // --- menu management ---------------------------------------------
  async function loadMenus() {
    try {
      var data = await A.request("/api/admin/menus", { token: state.token });
      state.categories = data.categories || [];
      renderMenuManage();
      renderCategoryOptions();
    } catch (e) {
      toast(e.detail || "메뉴 불러오기 실패");
    }
  }

  function renderCategoryOptions() {
    var sel = $("new-menu-cat");
    sel.innerHTML = "";
    state.categories.forEach(function (c) {
      var opt = document.createElement("option");
      opt.value = c.id;
      opt.textContent = c.name;
      sel.appendChild(opt);
    });
  }

  function renderMenuManage() {
    var root = $("menu-manage-root");
    root.innerHTML = "";
    state.categories.forEach(function (c) {
      var card = document.createElement("div");
      card.className = "card";
      card.innerHTML = "<h3>" + escapeHtml(c.name) + "</h3>";
      c.menus.forEach(function (m) {
        var row = document.createElement("div");
        row.className = "row space";
        row.style.padding = "0.35rem 0";
        row.style.borderBottom = "1px solid var(--line)";
        row.innerHTML =
          "<span>" + escapeHtml(m.name) + " · " + A.formatWon(m.price) + "</span>";
        var actions = document.createElement("div");
        actions.className = "row";
        var edit = document.createElement("button");
        edit.className = "ghost";
        edit.textContent = "가격수정";
        edit.onclick = function () {
          editMenuPrice(m);
        };
        var del = document.createElement("button");
        del.className = "ghost";
        del.textContent = "삭제";
        del.onclick = function () {
          deleteMenu(m);
        };
        actions.appendChild(edit);
        actions.appendChild(del);
        row.appendChild(actions);
        card.appendChild(row);
      });
      if (c.menus.length === 0) {
        card.innerHTML += '<p class="muted">메뉴가 없습니다.</p>';
      }
      root.appendChild(card);
    });
  }

  async function createCategory() {
    var name = $("new-cat-name").value.trim();
    if (!name) {
      toast("카테고리 이름을 입력하세요.");
      return;
    }
    try {
      await A.request("/api/admin/categories", {
        method: "POST",
        token: state.token,
        body: { name: name, display_order: Number($("new-cat-order").value) || 0 },
      });
      $("new-cat-name").value = "";
      toast("카테고리를 추가했습니다.");
      loadMenus();
    } catch (e) {
      toast(e.detail || "추가 실패");
    }
  }

  async function createMenu() {
    var body = {
      name: $("new-menu-name").value.trim(),
      price: Number($("new-menu-price").value),
      category_id: Number($("new-menu-cat").value),
      display_order: Number($("new-menu-order").value) || 0,
      description: $("new-menu-desc").value.trim() || null,
      image_url: $("new-menu-img").value.trim() || null,
    };
    if (!body.name || !body.category_id) {
      toast("이름과 카테고리를 확인하세요.");
      return;
    }
    try {
      await A.request("/api/admin/menus", {
        method: "POST",
        token: state.token,
        body: body,
      });
      $("new-menu-name").value = "";
      $("new-menu-price").value = "";
      $("new-menu-desc").value = "";
      $("new-menu-img").value = "";
      toast("메뉴를 추가했습니다.");
      loadMenus();
    } catch (e) {
      toast(e.detail || "추가 실패");
    }
  }

  async function editMenuPrice(m) {
    var next = window.prompt("새 가격(원)", m.price);
    if (next == null) return;
    var price = Number(next);
    if (isNaN(price) || price < 0) {
      toast("가격은 0 이상의 숫자여야 합니다.");
      return;
    }
    try {
      await A.request("/api/admin/menus/" + m.id, {
        method: "PUT",
        token: state.token,
        body: { price: price },
      });
      toast("가격을 수정했습니다.");
      loadMenus();
    } catch (e) {
      toast(e.detail || "수정 실패");
    }
  }

  async function deleteMenu(m) {
    if (!window.confirm("'" + m.name + "' 메뉴를 삭제할까요?")) return;
    try {
      await A.request("/api/admin/menus/" + m.id, {
        method: "DELETE",
        token: state.token,
      });
      toast("메뉴를 삭제했습니다.");
      loadMenus();
    } catch (e) {
      toast(e.detail || "삭제 실패");
    }
  }

  // --- tabs + wiring ------------------------------------------------
  function switchTab(tab) {
    document.querySelectorAll(".tabs button").forEach(function (b) {
      b.classList.toggle("active", b.getAttribute("data-tab") === tab);
    });
    $("tab-dashboard").classList.toggle("hidden", tab !== "dashboard");
    $("tab-tables").classList.toggle("hidden", tab !== "tables");
    $("tab-menus").classList.toggle("hidden", tab !== "menus");
    if (tab === "dashboard") loadDashboard();
    if (tab === "tables") loadTablesConfig();
    if (tab === "menus") loadMenus();
  }

  function wire() {
    $("login-submit").onclick = login;
    $("logout").onclick = logout;
    $("admin-pw").onclick = openAdminPasswordChange;
    $("modal-close").onclick = closeModal;
    $("modal-backdrop").onclick = function (e) {
      if (e.target === $("modal-backdrop")) closeModal();
    };
    $("new-table-submit").onclick = createTable;
    $("new-cat-submit").onclick = createCategory;
    $("new-menu-submit").onclick = createMenu;
    document.querySelectorAll(".tabs button").forEach(function (b) {
      b.onclick = function () {
        switchTab(b.getAttribute("data-tab"));
      };
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    wire();
    boot();
  });
})();
