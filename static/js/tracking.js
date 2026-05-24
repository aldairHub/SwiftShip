const fmt = {
    currency: v => `$${parseFloat(v).toFixed(2)}`,
    percent:  v => `${(parseFloat(v) * 100).toFixed(1)}%`,
};

const STATUS_COLORS = {
    Pending:   'badge-Pending',
    Shipped:   'badge-Shipped',
    Delivered: 'badge-Delivered',
    Cancelled: 'badge-Cancelled',
    Returned:  'badge-Returned',
};

let debounceTimer = null;
let currentOrders = [];
let currentPage   = 1;
let totalOrders   = 0;
const PAGE_SIZE   = 25;

function renderTable(orders, total, page) {
    currentOrders = orders;
    totalOrders   = total;
    currentPage   = page;

    const tbody = document.getElementById('tracking-tbody');
    const meta  = document.getElementById('search-meta');

    if (!orders.length) {
        tbody.innerHTML = '<tr><td colspan="9" class="empty-msg">No se encontraron pedidos.</td></tr>';
        meta.textContent = 'Sin resultados';
        renderPagination(0, 1);
        return;
    }

    const start = (page - 1) * PAGE_SIZE + 1;
    const end   = Math.min(page * PAGE_SIZE, total);
    meta.textContent = `Mostrando ${start}–${end} de ${total} pedidos`;

    tbody.innerHTML = orders.map((o, i) => `
        <tr>
            <td style="color: var(--accent); font-weight:600">${o.order_id}</td>
            <td>${o.order_date}</td>
            <td>${o.customer_name}</td>
            <td>${o.product_name}</td>
            <td>${o.category}</td>
            <td>${o.country}</td>
            <td>${fmt.currency(o.total_amount)}</td>
            <td><span class="badge ${STATUS_COLORS[o.status] || ''}">${o.status}</span></td>
            <td><button class="btn-detail" data-index="${i}">Ver detalle</button></td>
        </tr>
    `).join('');

    document.querySelectorAll('.btn-detail').forEach(btn => {
        btn.addEventListener('click', () => openDetail(currentOrders[parseInt(btn.dataset.index)]));
    });

    renderPagination(total, page);
}

function renderPagination(total, page) {
    const totalPages = Math.ceil(total / PAGE_SIZE);
    const container  = document.getElementById('pagination');
    if (!container) return;
    if (totalPages <= 1) { container.innerHTML = ''; return; }

    let html = '';
    for (let i = 1; i <= totalPages; i++) {
        if (i === 1 || i === totalPages || (i >= page - 2 && i <= page + 2)) {
            html += `<button class="${i === page ? 'active' : ''}" data-page="${i}">${i}</button>`;
        } else if (i === page - 3 || i === page + 3) {
            html += `<button disabled>…</button>`;
        }
    }
    container.innerHTML = html;
    container.querySelectorAll('button[data-page]').forEach(btn => {
        btn.addEventListener('click', () => fetchOrders(parseInt(btn.dataset.page)));
    });
}

function openDetail(o) {
    document.getElementById('detail-order-id').textContent = o.order_id;
    document.getElementById('detail-date').textContent     = `Fecha: ${o.order_date}`;

    const badge = document.getElementById('detail-status-badge');
    badge.textContent = o.status;
    badge.className   = `badge ${STATUS_COLORS[o.status] || ''}`;

    document.getElementById('d-customer').textContent = o.customer_name;
    document.getElementById('d-city').textContent     = o.city;
    document.getElementById('d-state').textContent    = o.state;
    document.getElementById('d-country').textContent  = o.country;

    document.getElementById('d-product').textContent  = o.product_name;
    document.getElementById('d-category').textContent = o.category;
    document.getElementById('d-brand').textContent    = o.brand;
    document.getElementById('d-quantity').textContent = o.quantity;

    document.getElementById('d-price').textContent    = fmt.currency(o.unit_price);
    document.getElementById('d-discount').textContent = fmt.percent(o.discount);
    document.getElementById('d-tax').textContent      = fmt.currency(o.tax);
    document.getElementById('d-shipping').textContent = fmt.currency(o.shipping_cost);
    document.getElementById('d-total').textContent    = fmt.currency(o.total_amount);
    document.getElementById('d-payment').textContent  = o.payment_method;

    document.getElementById('detail-overlay').classList.add('open');
}

function closeDetail() {
    document.getElementById('detail-overlay').classList.remove('open');
}

async function fetchOrders(page = 1) {
    const q      = document.getElementById('search-input').value.trim();
    const status = document.getElementById('status-filter').value;

    const params = new URLSearchParams();
    if (status) params.append('status', status);
    params.append('page',  page);
    params.append('limit', PAGE_SIZE);

    try {
        let json;
        if (q) {
            // Búsqueda de texto libre
            params.append('q', q);
            const res = await fetch(`/api/orders/search?${params}`);
            const arr = await res.json();
            json = { data: arr, total: arr.length, page: 1 };
        } else {
            // Listado paginado normal
            const res = await fetch(`/api/orders/?${params}`);
            json = await res.json();
        }
        renderTable(json.data, json.total, json.page);
    } catch {
        document.getElementById('tracking-tbody').innerHTML =
            '<tr><td colspan="9" class="empty-msg">Error al cargar los datos.</td></tr>';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    fetchOrders();

    document.getElementById('search-input').addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => fetchOrders(1), 300);
    });

    document.getElementById('status-filter').addEventListener('change', () => fetchOrders(1));
    document.getElementById('detail-close').addEventListener('click', closeDetail);
    document.getElementById('detail-overlay').addEventListener('click', e => {
        if (e.target === document.getElementById('detail-overlay')) closeDetail();
    });
});