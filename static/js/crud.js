// ── CONFIGURACIÓN DE COLECCIONES ──────────────────────────────
const COLLECTIONS = {
  pedidos: {
    label: "Pedidos",
    idField: "order_id",
    columns: ["order_id", "order_date", "customer_name", "product_name", "category", "country", "total_amount", "status"],
    headers: ["Order ID", "Fecha", "Cliente", "Producto", "Categoría", "País", "Total", "Estado"],
    fields: [
      { key: "order_id",       label: "Order ID",        type: "text" },
      { key: "order_date",     label: "Fecha",           type: "text" },
      { key: "customer_id",    label: "Customer ID",     type: "text" },
      { key: "customer_name",  label: "Cliente",         type: "text" },
      { key: "product_id",     label: "Product ID",      type: "text" },
      { key: "product_name",   label: "Producto",        type: "text" },
      { key: "category",       label: "Categoría",       type: "text" },
      { key: "brand",          label: "Marca",           type: "text" },
      { key: "quantity",       label: "Cantidad",        type: "number" },
      { key: "unit_price",     label: "Precio unitario", type: "number" },
      { key: "discount",       label: "Descuento",       type: "number" },
      { key: "total_amount",   label: "Total",           type: "number" },
      { key: "payment_method", label: "Método de pago",  type: "text" },
      { key: "status",         label: "Estado",          type: "text" },
      { key: "country",        label: "País",            type: "text" },
      { key: "seller_id",      label: "Seller ID",       type: "text" },
    ],
  },
  clientes: {
    label: "Clientes",
    idField: "customer_id",
    columns: ["customer_id", "name", "city", "state", "country"],
    headers: ["Customer ID", "Nombre", "Ciudad", "Estado", "País"],
    fields: [
      { key: "customer_id", label: "Customer ID", type: "text" },
      { key: "name",        label: "Nombre",      type: "text" },
      { key: "city",        label: "Ciudad",      type: "text" },
      { key: "state",       label: "Estado",      type: "text" },
      { key: "country",     label: "País",        type: "text" },
    ],
  },
  productos: {
    label: "Productos",
    idField: "product_id",
    columns: ["product_id", "name", "category", "brand", "unit_price"],
    headers: ["Product ID", "Nombre", "Categoría", "Marca", "Precio"],
    fields: [
      { key: "product_id",  label: "Product ID", type: "text" },
      { key: "name",        label: "Nombre",     type: "text" },
      { key: "category",    label: "Categoría",  type: "text" },
      { key: "brand",       label: "Marca",      type: "text" },
      { key: "unit_price",  label: "Precio",     type: "number" },
    ],
  },
  vendedores: {
    label: "Vendedores",
    idField: "seller_id",
    columns: ["seller_id", "name", "email", "country", "rating", "active"],
    headers: ["Seller ID", "Nombre", "Email", "País", "Rating", "Activo"],
    fields: [
      { key: "seller_id",   label: "Seller ID", type: "text" },
      { key: "name",        label: "Nombre",    type: "text" },
      { key: "email",       label: "Email",     type: "text" },
      { key: "phone",       label: "Teléfono",  type: "text" },
      { key: "city",        label: "Ciudad",    type: "text" },
      { key: "country",     label: "País",      type: "text" },
      { key: "rating",      label: "Rating",    type: "number" },
      { key: "active",      label: "Activo",    type: "text" },
      { key: "joined_date", label: "Registro",  type: "text" },
    ],
  },
  categorias: {
    label: "Categorías",
    idField: "name",
    columns: ["name"],
    headers: ["Nombre"],
    fields: [{ key: "name", label: "Nombre", type: "text" }],
  },
  marcas: {
    label: "Marcas",
    idField: "name",
    columns: ["name"],
    headers: ["Nombre"],
    fields: [{ key: "name", label: "Nombre", type: "text" }],
  },
  metodos_pago: {
    label: "Métodos de Pago",
    idField: "name",
    columns: ["name"],
    headers: ["Nombre"],
    fields: [{ key: "name", label: "Nombre", type: "text" }],
  },
  estados: {
    label: "Estados",
    idField: "name",
    columns: ["name"],
    headers: ["Nombre"],
    fields: [{ key: "name", label: "Nombre", type: "text" }],
  },
  ubicaciones: {
    label: "Ubicaciones",
    idField: "location_id",
    columns: ["location_id", "city", "state", "country"],
    headers: ["ID", "Ciudad", "Estado", "País"],
    fields: [
      { key: "location_id", label: "ID",      type: "number" },
      { key: "city",        label: "Ciudad",  type: "text" },
      { key: "state",       label: "Estado",  type: "text" },
      { key: "country",     label: "País",    type: "text" },
    ],
  },
};

// ── ESTADO ────────────────────────────────────────────────────
let state = {
  collection: "pedidos",
  page:       1,
  total:      0,
  editingId:  null,
  deletingId: null,
  debounce:   null,
};

const PAGE_SIZE = 50;

// ── HELPERS ───────────────────────────────────────────────────
function getCfg() { return COLLECTIONS[state.collection]; }

function fmtCell(key, val) {
  if (val === undefined || val === null) return "—";
  if (key === "total_amount" || key === "unit_price") return `$${parseFloat(val).toFixed(2)}`;
  if (key === "active") return val ? "✅" : "❌";
  if (key === "rating")  return `★ ${parseFloat(val).toFixed(1)}`;
  return String(val);
}

// ── RENDER TABLA ──────────────────────────────────────────────
function renderTable(docs, total, page) {
  state.total = total;
  state.page  = page;
  const cfg   = getCfg();

  // Headers
  document.getElementById("crud-thead").innerHTML = `<tr>
    ${cfg.headers.map(h => `<th>${h}</th>`).join("")}
    <th>Acciones</th>
  </tr>`;

  // Meta
  const start = (page - 1) * PAGE_SIZE + 1;
  const end   = Math.min(page * PAGE_SIZE, total);
  document.getElementById("crud-meta").textContent =
    total ? `Mostrando ${start}–${end} de ${total} documentos` : "Sin resultados";

  // Rows
  const tbody = document.getElementById("crud-tbody");
  if (!docs.length) {
    tbody.innerHTML = `<tr><td colspan="${cfg.columns.length + 1}" class="empty-msg">Sin documentos.</td></tr>`;
    renderPagination(total, page);
    return;
  }

  tbody.innerHTML = docs.map(doc => `
    <tr>
      ${cfg.columns.map(col => `<td>${fmtCell(col, doc[col])}</td>`).join("")}
      <td>
        <button class="btn-edit"   data-id="${doc[cfg.idField]}">Editar</button>
        <button class="btn-delete" data-id="${doc[cfg.idField]}">Eliminar</button>
      </td>
    </tr>
  `).join("");

  document.querySelectorAll(".btn-edit").forEach(btn =>
    btn.addEventListener("click", () => openEdit(btn.dataset.id, docs))
  );
  document.querySelectorAll(".btn-delete").forEach(btn =>
    btn.addEventListener("click", () => openConfirm(btn.dataset.id))
  );

  renderPagination(total, page);
}

function renderPagination(total, page) {
  const totalPages = Math.ceil(total / PAGE_SIZE);
  const container  = document.getElementById("crud-pagination");
  if (totalPages <= 1) { container.innerHTML = ""; return; }

  let html = "";
  for (let i = 1; i <= totalPages; i++) {
    if (i === 1 || i === totalPages || (i >= page - 2 && i <= page + 2)) {
      html += `<button class="${i === page ? "active" : ""}" data-page="${i}">${i}</button>`;
    } else if (i === page - 3 || i === page + 3) {
      html += `<button disabled>…</button>`;
    }
  }
  container.innerHTML = html;
  container.querySelectorAll("button[data-page]").forEach(btn =>
    btn.addEventListener("click", () => fetchDocs(parseInt(btn.dataset.page)))
  );
}

// ── FETCH ─────────────────────────────────────────────────────
async function fetchDocs(page = 1) {
  const q = document.getElementById("crud-search").value.trim();
  const params = new URLSearchParams({ page, limit: PAGE_SIZE });
  if (q) params.append("q", q);

  try {
    const res  = await fetch(`/api/crud/${state.collection}?${params}`);
    const json = await res.json();
    renderTable(json.data, json.total, json.page);
  } catch {
    document.getElementById("crud-tbody").innerHTML =
      `<tr><td class="empty-msg">Error al cargar los datos.</td></tr>`;
  }
}

// ── MODAL CREAR/EDITAR ────────────────────────────────────────
function buildForm(data = {}) {
  const cfg = getCfg();
  return cfg.fields.map(f => `
    <div class="form-field">
      <label>${f.label}</label>
      <input type="${f.type}" name="${f.key}" value="${data[f.key] ?? ""}" />
    </div>
  `).join("");
}

function openCreate() {
  state.editingId = null;
  document.getElementById("modal-title").textContent = "Nuevo documento";
  document.getElementById("modal-form").innerHTML = buildForm();
  document.getElementById("modal-overlay").classList.add("open");
}

function openEdit(id, docs) {
  const cfg = getCfg();
  const doc = docs.find(d => String(d[cfg.idField]) === String(id));
  if (!doc) return;
  state.editingId = id;
  document.getElementById("modal-title").textContent = "Editar documento";
  document.getElementById("modal-form").innerHTML = buildForm(doc);
  document.getElementById("modal-overlay").classList.add("open");
}

function closeModal() {
  document.getElementById("modal-overlay").classList.remove("open");
  state.editingId = null;
}

async function saveDocument() {
  const cfg    = getCfg();
  const inputs = document.querySelectorAll("#modal-form input");
  const body   = {};
  inputs.forEach(inp => {
    if (inp.value !== "") {
      body[inp.name] = inp.type === "number" ? parseFloat(inp.value) : inp.value;
    }
  });

  try {
    let res;
    if (state.editingId) {
      res = await fetch(`/api/crud/${state.collection}/${state.editingId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
    } else {
      res = await fetch(`/api/crud/${state.collection}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
    }

    if (res.ok) {
      closeModal();
      fetchDocs(state.page);
    } else {
      const err = await res.json();
      alert(err.error || "Error al guardar");
    }
  } catch {
    alert("Error de conexión");
  }
}

// ── MODAL ELIMINAR ────────────────────────────────────────────
function openConfirm(id) {
  state.deletingId = id;
  document.getElementById("confirm-overlay").classList.add("open");
}

function closeConfirm() {
  document.getElementById("confirm-overlay").classList.remove("open");
  state.deletingId = null;
}

async function deleteDocument() {
  try {
    const res = await fetch(`/api/crud/${state.collection}/${state.deletingId}`, {
      method: "DELETE",
    });
    if (res.ok) {
      closeConfirm();
      fetchDocs(state.page);
    } else {
      alert("Error al eliminar");
    }
  } catch {
    alert("Error de conexión");
  }
}

// ── INICIALIZACIÓN ────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  fetchDocs();

  document.getElementById("collection-select").addEventListener("change", e => {
    state.collection = e.target.value;
    state.page = 1;
    fetchDocs();
  });

  document.getElementById("crud-search").addEventListener("input", () => {
    clearTimeout(state.debounce);
    state.debounce = setTimeout(() => fetchDocs(1), 300);
  });

  document.getElementById("btn-nuevo").addEventListener("click", openCreate);
  document.getElementById("modal-close").addEventListener("click", closeModal);
  document.getElementById("modal-cancel").addEventListener("click", closeModal);
  document.getElementById("modal-save").addEventListener("click", saveDocument);
  document.getElementById("confirm-close").addEventListener("click", closeConfirm);
  document.getElementById("confirm-cancel").addEventListener("click", closeConfirm);
  document.getElementById("confirm-delete").addEventListener("click", deleteDocument);

  document.getElementById("modal-overlay").addEventListener("click", e => {
    if (e.target === document.getElementById("modal-overlay")) closeModal();
  });
  document.getElementById("confirm-overlay").addEventListener("click", e => {
    if (e.target === document.getElementById("confirm-overlay")) closeConfirm();
  });
});