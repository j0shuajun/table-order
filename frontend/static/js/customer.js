// Customer app: table auto-login, menu browsing, cart, order + current orders.
(function () {
  "use strict";
  var A = window.API;

  var state = {
    token: null,
    info: null, // {store_id, table_number, table_id}
    menu: [], // categories
    cart: {}, // menu_id -> {menu, quantity}
  };

  var el = {};
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

  // --- auth ---------------------------------------------------------
  function showAuth(message) {
    $("app-view").classList.add("hidden");
    $("auth-view").classList.remove("hidden");
    $("auth-error").textContent = message || "";
    var info = A.getTableInfo();
    if (info) {
      $("auth-store").value = info.store_id || "store001";
      $("auth-table").value = info.table_number || "";
    }
  }

  function showApp() {
    $("auth-view").classList.add("hidden");
    $("app-view").classList.remove("hidden");
    $("table-label").textContent =
      (state.info && state.info.table_number) || "테이블";
  }

  async function authenticate(store_id, table_number, password) {
    var res = await A.request("/api/table/auth", {
      method: "POST",
      body: { store_id: store_id, table_number: table_number, password: password },
    });
    state.token = res.token;
    state.info = {
      store_id: res.store_id,
      table_number: res.table_number,
      table_id: res.table_id,
    };
    A.setTableToken(res.token);
    A.setTableInfo(state.info);
  }

  // Try stored token; on expiry, silently re-auth is not possible without the
  // password, so we fall back to the auth form.
  async function boot() {
    state.token = A.getTableToken();
    state.info = A.getTableInfo();
    if (!state.token) {
      showAuth();
      return;
    }
    try {
      await loadMenu();
      showApp();
      loadCurrentOrders();
    } catch (e) {
      if (e.status === 401) {
        A.setTableToken(null);
        showAuth("세션이 만료되었습니다. 다시 연결해 주세요.");
      } else {
        showAuth(e.detail || "메뉴를 불러오지 못했습니다.");
      }
    }
  }

  // --- menu + cart --------------------------------------------------
  async function loadMenu() {
    var data = await A.request("/api/menu", { token: state.token });
    state.menu = data.categories || [];
    renderMenu();
  }

  function renderMenu() {
    var root = $("menu-root");
    root.innerHTML = "";
    state.menu.forEach(function (cat) {
      var section = document.createElement("div");
      section.className = "menu-category";
      var h = document.createElement("h2");
      h.textContent = cat.name;
      section.appendChild(h);
      var list = document.createElement("div");
      list.className = "grid menu-list";
      cat.menus.forEach(function (m) {
        list.appendChild(menuCard(m));
      });
      section.appendChild(list);
      root.appendChild(section);
    });
  }

  function menuCard(m) {
    var card = document.createElement("div");
    card.className = "card menu-item";
    var img = document.createElement("img");
    img.src = m.image_url || "https://placehold.co/300x200?text=Menu";
    img.alt = m.name;
    img.onerror = function () {
      img.src = "https://placehold.co/300x200?text=Menu";
    };
    var name = document.createElement("div");
    name.innerHTML = "<strong>" + escapeHtml(m.name) + "</strong>";
    var desc = document.createElement("div");
    desc.className = "muted";
    desc.style.fontSize = "0.85rem";
    desc.textContent = m.description || "";
    var price = document.createElement("div");
    price.className = "price";
    price.textContent = A.formatWon(m.price);
    var add = document.createElement("button");
    add.textContent = "담기";
    add.onclick = function () {
      addToCart(m);
    };
    card.appendChild(img);
    card.appendChild(name);
    card.appendChild(desc);
    card.appendChild(price);
    card.appendChild(add);
    return card;
  }

  function addToCart(m) {
    var line = state.cart[m.id];
    if (line) line.quantity += 1;
    else state.cart[m.id] = { menu: m, quantity: 1 };
    renderCart();
    toast(m.name + " 담음");
  }

  function changeQty(menuId, delta) {
    var line = state.cart[menuId];
    if (!line) return;
    line.quantity += delta;
    if (line.quantity <= 0) delete state.cart[menuId];
    renderCart();
  }

  function cartItems() {
    return Object.keys(state.cart).map(function (id) {
      return state.cart[id];
    });
  }

  function renderCart() {
    var lines = $("cart-lines");
    lines.innerHTML = "";
    var items = cartItems();
    var total = 0;
    items.forEach(function (line) {
      total += line.menu.price * line.quantity;
      var row = document.createElement("div");
      row.className = "cart-line";
      var label = document.createElement("span");
      label.textContent = line.menu.name;
      var right = document.createElement("div");
      right.className = "qty";
      var minus = document.createElement("button");
      minus.textContent = "−";
      minus.onclick = function () {
        changeQty(line.menu.id, -1);
      };
      var q = document.createElement("span");
      q.textContent = line.quantity;
      var plus = document.createElement("button");
      plus.textContent = "+";
      plus.onclick = function () {
        changeQty(line.menu.id, 1);
      };
      var sub = document.createElement("span");
      sub.style.minWidth = "70px";
      sub.style.textAlign = "right";
      sub.textContent = A.formatWon(line.menu.price * line.quantity);
      right.appendChild(minus);
      right.appendChild(q);
      right.appendChild(plus);
      right.appendChild(sub);
      row.appendChild(label);
      row.appendChild(right);
      lines.appendChild(row);
    });
    if (items.length === 0) {
      lines.innerHTML = '<p class="muted">담은 메뉴가 없습니다.</p>';
    }
    $("cart-total").textContent = "합계 " + A.formatWon(total);
    $("cart-submit").disabled = items.length === 0;
  }

  async function submitOrder() {
    var items = cartItems().map(function (line) {
      return { menu_id: line.menu.id, quantity: line.quantity };
    });
    if (items.length === 0) return;
    $("cart-submit").disabled = true;
    try {
      var res = await A.request("/api/orders", {
        method: "POST",
        token: state.token,
        body: { items: items },
      });
      state.cart = {};
      renderCart();
      toast("주문 완료 · " + res.order_number + " (" + A.formatWon(res.total_amount) + ")");
      loadCurrentOrders();
    } catch (e) {
      if (e.status === 401) {
        A.setTableToken(null);
        showAuth("세션이 만료되었습니다. 다시 연결해 주세요.");
      } else {
        toast(e.detail || "주문에 실패했습니다.");
        $("cart-submit").disabled = false;
      }
    }
  }

  // --- current orders ----------------------------------------------
  async function loadCurrentOrders() {
    try {
      var data = await A.request("/api/orders/current", { token: state.token });
      renderCurrentOrders(data);
    } catch (e) {
      // non-fatal for the menu screen
    }
  }

  function renderCurrentOrders(data) {
    $("session-total").textContent = "합계 " + A.formatWon(data.session_total);
    var root = $("orders-root");
    root.innerHTML = "";
    if (!data.orders || data.orders.length === 0) {
      root.innerHTML = '<p class="muted">아직 주문이 없습니다.</p>';
      return;
    }
    data.orders.forEach(function (o) {
      var card = document.createElement("div");
      card.className = "card";
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
          "<span>" +
          escapeHtml(it.menu_name) +
          " × " +
          it.quantity +
          "</span><span>" +
          A.formatWon(it.line_total) +
          "</span>";
        card.appendChild(row);
      });
      var total = document.createElement("div");
      total.className = "row space";
      total.style.marginTop = "0.4rem";
      total.innerHTML = "<span class='muted'>주문 합계</span><strong>" + A.formatWon(o.total_amount) + "</strong>";
      card.appendChild(total);
      root.appendChild(card);
    });
  }

  function statusBadge(status) {
    var label = { pending: "접수", preparing: "준비중", completed: "완료" }[status] || status;
    return "<span class='badge " + status + "'>" + label + "</span>";
  }

  function escapeHtml(s) {
    return (s || "").replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  // --- tabs + wiring ------------------------------------------------
  function switchTab(tab) {
    document.querySelectorAll(".tabs button").forEach(function (b) {
      b.classList.toggle("active", b.getAttribute("data-tab") === tab);
    });
    $("tab-menu").classList.toggle("hidden", tab !== "menu");
    $("cart-bar").classList.toggle("hidden", tab !== "menu");
    $("tab-orders").classList.toggle("hidden", tab !== "orders");
    if (tab === "orders") loadCurrentOrders();
  }

  function wire() {
    $("auth-submit").onclick = async function () {
      try {
        await authenticate(
          $("auth-store").value.trim(),
          $("auth-table").value.trim(),
          $("auth-pw").value
        );
        showApp();
        await loadMenu();
        loadCurrentOrders();
      } catch (e) {
        $("auth-error").textContent = e.detail || "연결에 실패했습니다.";
      }
    };
    $("cart-clear").onclick = function () {
      state.cart = {};
      renderCart();
    };
    $("cart-submit").onclick = submitOrder;
    document.querySelectorAll(".tabs button").forEach(function (b) {
      b.onclick = function () {
        switchTab(b.getAttribute("data-tab"));
      };
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    wire();
    renderCart();
    boot();
  });
})();
