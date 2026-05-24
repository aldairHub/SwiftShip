// ── CONSTANTES ────────────────────────────────────────────────
const STATUS_COLORS = {
  Pending: "#F59E0B",
  Shipped: "#3B82F6",
  Delivered: "#10B981",
  Cancelled: "#EF4444",
  Returned: "#8B5CF6",
};

// ── ESTADO GLOBAL ─────────────────────────────────────────────
const State = {
  page: 1,
  pageSize: 25,
  sortCol: "OrderDate",
  sortDir: "desc",
  total: 0,
  allOrders: [],
  filters: {},
};

// ── UTILIDADES ────────────────────────────────────────────────
const fmt = {
  currency: (v) => `$${parseFloat(v).toFixed(2)}`,
  percent: (v) => `${(parseFloat(v) * 100).toFixed(1)}%`,
  pct: (v) => `${parseFloat(v).toFixed(1)}%`,
};

function buildQueryString(filters) {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(filters)) {
    if (!v) continue;
    if (Array.isArray(v)) v.forEach((x) => p.append(k, x));
    else p.append(k, v);
  }
  return p.toString();
}

// ── FILTER MANAGER ────────────────────────────────────────────
const FilterManager = {
  getActiveFilters() {
    const statusEl = document.getElementById("status");
    const status = [...statusEl.selectedOptions].map((o) => o.value);
    return {
      date_from: document.getElementById("date_from").value || null,
      date_to: document.getElementById("date_to").value || null,
      status: status.length ? status : null,
      country: document.getElementById("country").value || null,
      category: document.getElementById("category").value || null,
      brand: document.getElementById("brand").value || null,
      payment_method: document.getElementById("payment_method").value || null,
    };
  },

  reset() {
    document.getElementById("date_from").value = "";
    document.getElementById("date_to").value = "";
    document.getElementById("status").selectedIndex = -1;
    ["country", "category", "brand", "payment_method"].forEach((id) => {
      document.getElementById(id).value = "";
    });
  },
};

// ── KPI MANAGER ───────────────────────────────────────────────
const KPIManager = {
  showSpinners() {
    [
      "val-revenue",
      "val-discount",
      "val-brand",
      "val-payment",
      "val-correlation",
    ].forEach((id) => {
      document.getElementById(id).innerHTML =
        '<span class="kpi-spinner"></span>';
    });
  },

  render(data) {
    document.getElementById("val-revenue").textContent =
      "$" + (data.total_revenue / 1_000_000).toFixed(1) + "M";
    document.getElementById("val-discount").textContent = fmt.pct(
      data.avg_discount_pct,
    );
    document.getElementById("val-brand").textContent =
      data.top_brand_by_quantity || "N/A";
    document.getElementById("val-payment").textContent =
      data.top_payment_method || "N/A";
    document.getElementById("val-correlation").textContent =
      data.discount_cancellation_correlation !== undefined
        ? data.discount_cancellation_correlation.toFixed(3)
        : "N/A";
  },

  showError() {
    [
      "val-revenue",
      "val-discount",
      "val-brand",
      "val-payment",
      "val-correlation",
    ].forEach((id) => {
      document.getElementById(id).textContent = "Error";
    });
  },

  async fetch(filters) {
    this.showSpinners();
    try {
      const qs = buildQueryString(filters);
      const res = await fetch(`/api/orders/summary?${qs}`);
      if (!res.ok) throw new Error(res.status);
      const data = await res.json();
      this.render(data);
    } catch {
      this.showError();
    }
  },
};

// ── TABLE MANAGER ─────────────────────────────────────────────
const TableManager = {
  render(orders) {
    State.allOrders = orders;
    this.renderPage();
  },

  renderPage() {
    const start = (State.page - 1) * State.pageSize;
    const end = Math.min(start + State.pageSize, State.total);
    const tbody = document.getElementById("orders-tbody");

    if (!State.allOrders.length) {
      tbody.innerHTML =
        '<tr><td colspan="16" class="empty-msg">No se encontraron pedidos.</td></tr>';
      document.getElementById("table-count").textContent = "Sin resultados";
      document.getElementById("pagination").innerHTML = "";
      return;
    }

    tbody.innerHTML = State.allOrders
      .map(
        (r) => `
      <tr>
        <td>${r.order_id}</td>
        <td>${r.order_date}</td>
        <td>${r.customer_name}</td>
        <td>${r.product_name}</td>
        <td>${r.category}</td>
        <td>${r.brand}</td>
        <td>${r.quantity}</td>
        <td>${fmt.currency(r.unit_price)}</td>
        <td>${fmt.percent(r.discount)}</td>
        <td>${fmt.currency(r.tax)}</td>
        <td>${fmt.currency(r.shipping_cost)}</td>
        <td>${fmt.currency(r.total_amount)}</td>
        <td>${r.payment_method}</td>
        <td><span class="badge badge-${r.status}">${r.status}</span></td>
        <td>${r.city}</td>
        <td>${r.country}</td>
      </tr>
    `,
      )
      .join("");

    document.getElementById("table-count").textContent =
      `Mostrando ${start + 1}–${Math.min(start + State.pageSize, State.total)} de ${State.total} pedidos`;

    this.renderPagination();
    this.updateSortHeaders();
  },

  renderPagination() {
    const totalPages = Math.ceil(State.total / State.pageSize);
    const container = document.getElementById("pagination");
    if (totalPages <= 1) {
      container.innerHTML = "";
      return;
    }

    let html = "";
    const current = State.page;
    for (let i = 1; i <= totalPages; i++) {
      if (
        i === 1 ||
        i === totalPages ||
        (i >= current - 2 && i <= current + 2)
      ) {
        html += `<button class="${i === current ? "active" : ""}" data-page="${i}">${i}</button>`;
      } else if (i === current - 3 || i === current + 3) {
        html += `<button disabled>…</button>`;
      }
    }
    container.innerHTML = html;
    container.querySelectorAll("button[data-page]").forEach((btn) => {
      btn.addEventListener("click", () => {
        State.page = parseInt(btn.dataset.page);
        this.fetch(State.filters);
      });
    });
  },

  updateSortHeaders() {
    document.querySelectorAll("thead th.sortable").forEach((th) => {
      th.classList.remove("sort-asc", "sort-desc");
      if (th.dataset.col === State.sortCol)
        th.classList.add(State.sortDir === "asc" ? "sort-asc" : "sort-desc");
    });
  },

  bindSortHeaders() {
    document.querySelectorAll("thead th.sortable").forEach((th) => {
      th.addEventListener("click", () => {
        if (State.sortCol === th.dataset.col) {
          State.sortDir = State.sortDir === "asc" ? "desc" : "asc";
        } else {
          State.sortCol = th.dataset.col;
          State.sortDir = "asc";
        }
        State.page = 1;
        this.fetch(State.filters);
      });
    });
  },

  async fetch(filters) {
    const qs = buildQueryString({
      ...filters,
      page: State.page,
      limit: State.pageSize,
    });
    const res = await fetch(`/api/orders/?${qs}`);
    if (!res.ok) {
      document.getElementById("orders-tbody").innerHTML =
        '<tr><td colspan="16" class="empty-msg">Error al cargar los datos.</td></tr>';
      return;
    }
    const json = await res.json();
    State.total = json.total;
    State.page = json.page;
    this.render(json.data);
  },
};

// ── CHART MANAGER ─────────────────────────────────────────────
const ChartManager = {
  instances: {},

  destroy(id) {
    if (this.instances[id]) {
      this.instances[id].destroy();
      delete this.instances[id];
    }
  },

  renderBar(data) {
    this.destroy("bar");
    const ctx = document.getElementById("chart-bar").getContext("2d");
    if (!data.labels.length) {
      ctx.canvas.parentElement.innerHTML =
        '<div class="no-data">Sin datos para mostrar.</div>';
      return;
    }
    this.instances["bar"] = new Chart(ctx, {
      type: "bar",
      data: {
        labels: data.labels,
        datasets: [
          {
            label: "Ingresos (USD)",
            data: data.values,
            backgroundColor: "#4f8ef7",
            borderRadius: 4,
          },
        ],
      },
      options: {
        responsive: true,
        indexAxis: "y",
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: (c) => fmt.currency(c.raw) } },
        },
        scales: {
          x: { ticks: { color: "#8892a4" }, grid: { color: "#2e3250" } },
          y: { ticks: { color: "#8892a4" }, grid: { display: false } },
        },
      },
    });
  },

  renderLine(data) {
    this.destroy("line");
    const ctx = document.getElementById("chart-line").getContext("2d");
    if (!data.labels.length) {
      ctx.canvas.parentElement.innerHTML =
        '<div class="no-data">Sin datos para mostrar.</div>';
      return;
    }
    this.instances["line"] = new Chart(ctx, {
      type: "line",
      data: {
        labels: data.labels,
        datasets: [
          {
            label: "Pedidos",
            data: data.values,
            borderColor: "#7c3aed",
            backgroundColor: "rgba(124,58,237,0.15)",
            tension: 0.4,
            fill: true,
            pointRadius: 3,
          },
        ],
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          x: {
            ticks: { color: "#8892a4", maxTicksLimit: 12 },
            grid: { color: "#2e3250" },
          },
          y: { ticks: { color: "#8892a4" }, grid: { color: "#2e3250" } },
        },
      },
    });
  },

  renderPie(data) {
    this.destroy("pie");
    const ctx = document.getElementById("chart-pie").getContext("2d");
    if (!data.labels.length) {
      ctx.canvas.parentElement.innerHTML =
        '<div class="no-data">Sin datos para mostrar.</div>';
      return;
    }
    this.instances["pie"] = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: data.labels,
        datasets: [
          {
            data: data.values,
            backgroundColor: data.labels.map(
              (l) => STATUS_COLORS[l] || "#8892a4",
            ),
            borderWidth: 2,
            borderColor: "#1a1d27",
          },
        ],
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            position: "bottom",
            labels: { color: "#e2e8f0", padding: 12 },
          },
          tooltip: {
            callbacks: {
              label: (c) => {
                const total = c.dataset.data.reduce((a, b) => a + b, 0);
                return `${c.label}: ${c.raw} (${((c.raw / total) * 100).toFixed(1)}%)`;
              },
            },
          },
        },
      },
    });
  },

  renderHeatmap(data) {
    const el = document.getElementById("chart-heatmap");
    if (!data.x.length) {
      el.innerHTML = '<div class="no-data">Sin datos para mostrar.</div>';
      return;
    }
    Plotly.newPlot(
      el,
      [
        {
          type: "heatmap",
          x: data.x,
          y: data.y,
          z: data.z,
          colorscale: "Blues",
          hoverongaps: false,
          hovertemplate:
            "País: %{y}<br>Categoría: %{x}<br>Pedidos: %{z}<extra></extra>",
        },
      ],
      {
        paper_bgcolor: "#1a1d27",
        plot_bgcolor: "#1a1d27",
        font: { color: "#e2e8f0", size: 11 },
        margin: { t: 20, r: 20, b: 80, l: 100 },
        xaxis: { tickangle: -30 },
      },
      { responsive: true, displayModeBar: false },
    );
  },

  renderSankey(data) {
    const el = document.getElementById("chart-sankey");
    if (!data.nodes.length) {
      el.innerHTML = '<div class="no-data">Sin datos para mostrar.</div>';
      return;
    }
    const nodeIds = data.nodes.map((n) => n.id);
    const nodeLabels = data.nodes.map((n) => n.label);
    const sources = data.links.map((l) => nodeIds.indexOf(l.source));
    const targets = data.links.map((l) => nodeIds.indexOf(l.target));
    const values = data.links.map((l) => l.value);

    Plotly.newPlot(
      el,
      [
        {
          type: "sankey",
          orientation: "h",
          node: {
            pad: 15,
            thickness: 20,
            line: { color: "#2e3250", width: 0.5 },
            label: nodeLabels,
            color: "#4f8ef7",
          },
          link: {
            source: sources,
            target: targets,
            value: values,
            color: "rgba(79,142,247,0.3)",
          },
        },
      ],
      {
        paper_bgcolor: "#1a1d27",
        font: { color: "#e2e8f0", size: 11 },
        margin: { t: 20, r: 20, b: 20, l: 20 },
      },
      { responsive: true, displayModeBar: false },
    );
  },

  renderBubble(data) {
    this.destroy("bubble");
    const ctx = document.getElementById("chart-bubble").getContext("2d");
    if (!data.length) {
      ctx.canvas.parentElement.innerHTML =
        '<div class="no-data">Sin datos para mostrar.</div>';
      return;
    }
    this.instances["bubble"] = new Chart(ctx, {
      type: "bubble",
      data: {
        datasets: data.map((d, i) => ({
          label: d.category,
          data: [
            { x: d.avg_quantity, y: d.avg_total_amount, r: d.bubble_size / 3 },
          ],
          backgroundColor: `hsl(${(i * 47) % 360}, 65%, 55%)`,
        })),
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            position: "bottom",
            labels: { color: "#e2e8f0", padding: 8, boxWidth: 10 },
          },
          tooltip: {
            callbacks: {
              label: (c) => {
                const d = data[c.datasetIndex];
                return [
                  `Categoría: ${d.category}`,
                  `Qty Promedio: ${d.avg_quantity}`,
                  `Total Promedio: ${fmt.currency(d.avg_total_amount)}`,
                  `Costo Envío Prom: ${fmt.currency(d.avg_shipping_cost)}`,
                ];
              },
            },
          },
        },
        scales: {
          x: {
            title: { display: true, text: "Qty Promedio", color: "#8892a4" },
            ticks: { color: "#8892a4" },
            grid: { color: "#2e3250" },
          },
          y: {
            title: {
              display: true,
              text: "Total Promedio (USD)",
              color: "#8892a4",
            },
            ticks: { color: "#8892a4" },
            grid: { color: "#2e3250" },
          },
        },
      },
    });
  },

  renderTreemap(data) {
    const el = document.getElementById("chart-treemap");
    if (!data.length) {
      el.innerHTML = '<div class="no-data">Sin datos para mostrar.</div>';
      return;
    }

    const uniqueCategories = [...new Set(data.map((d) => d.category))];

    const labels = [];
    const parents = [];
    const values = [];

    uniqueCategories.forEach((cat) => {
      const catTotal = data
        .filter((d) => d.category === cat)
        .reduce((sum, d) => sum + d.total_amount, 0);
      labels.push(cat);
      parents.push("");
      values.push(catTotal);
    });

    data.forEach((d) => {
      labels.push(d.brand);
      parents.push(d.category);
      values.push(d.total_amount);
    });

    Plotly.purge(el);
    Plotly.newPlot(
      el,
      [
        {
          type: "treemap",
          labels,
          parents,
          values,
          texttemplate: "%{label}<br>$%{value:,.2f}",
          hovertemplate:
            "<b>%{label}</b><br>Total: $%{value:,.2f}<extra></extra>",
          marker: { colorscale: "Viridis" },
        },
      ],
      {
        paper_bgcolor: "#1a1d27",
        font: { color: "#e2e8f0", size: 11 },
        margin: { t: 20, r: 10, b: 10, l: 10 },
      },
      { responsive: true, displayModeBar: false },
    );
  },

  renderAll(payload) {
    // Destruir todos los canvas antes de redibujar
    ["bar", "line", "pie", "bubble"].forEach((id) => this.destroy(id));

    // Resetear contenedores de Plotly
    ["chart-heatmap", "chart-sankey", "chart-treemap"].forEach((id) => {
      Plotly.purge(document.getElementById(id));
    });

    this.renderBar(payload.bar_total_amount_by_country);
    this.renderLine(payload.line_orders_by_week);
    this.renderPie(payload.pie_order_status);
    this.renderHeatmap(payload.heatmap_country_category);
    this.renderSankey(payload.sankey_country_category_status);
    this.renderBubble(payload.bubble_category_metrics);
    this.renderTreemap(payload.treemap_category_brand);
  },

  async fetch(filters) {
    const qs = buildQueryString(filters);
    const res = await fetch(`/api/orders/charts?${qs}`);
    if (!res.ok) return;
    const data = await res.json();
    this.renderAll(data);
  },
};

// ── EXPORT MANAGER ────────────────────────────────────────────
const ExportManager = {
  bind() {
    document.getElementById("btn-export").addEventListener("click", () => {
      const qs = buildQueryString(State.filters);
      window.location.href = `/api/orders/export?${qs}`;
    });
  },
};

// ── INICIALIZACIÓN ────────────────────────────────────────────
async function loadAll(filters) {
  State.filters = filters;
  await Promise.all([
    TableManager.fetch(filters),
    KPIManager.fetch(filters),
    ChartManager.fetch(filters),
  ]);
}

document.addEventListener("DOMContentLoaded", () => {
  TableManager.bindSortHeaders();
  ExportManager.bind();

  document.getElementById("page-size").addEventListener("change", (e) => {
    State.pageSize = parseInt(e.target.value);
    State.page = 1;
    TableManager.renderPage();
  });

  document.getElementById("btn-apply").addEventListener("click", () => {
    const filters = FilterManager.getActiveFilters();
    loadAll(filters);
  });

  document.getElementById("btn-reset").addEventListener("click", () => {
    FilterManager.reset();
    loadAll({});
  });

  loadAll({});
});
