const fmt = {
    currency: v => v ? `$${parseFloat(v).toFixed(2)}` : '$0.00',
    rating: v => {
        const n = parseFloat(v);
        const cls = n >= 4.5 ? 'rating-high' : n >= 3.5 ? 'rating-mid' : 'rating-low';
        return `<span class="rating ${cls}">★ ${n.toFixed(1)}</span>`;
    },
    cancel: v => {
        const n = parseFloat(v || 0);
        const cls = n >= 20 ? 'cancel-high' : n >= 10 ? 'cancel-mid' : 'cancel-low';
        return `<span class="${cls}">${n.toFixed(1)}%</span>`;
    },
};

let debounceTimer = null;
let currentSellers = [];

async function fetchKPIs() {
    try {
        const res  = await fetch('/api/sellers/summary');
        const data = await res.json();
        document.getElementById('kpi-total').textContent      = data.total;
        document.getElementById('kpi-activos').textContent    = data.active;
        document.getElementById('kpi-calificacion').innerHTML = fmt.rating(data.avg_rating);
        document.getElementById('kpi-mejor').textContent      = data.top_seller;
    } catch {}
}

function renderTable(sellers, total, page) {
    currentSellers = sellers;
    const tbody = document.getElementById('sellers-tbody');
    const meta  = document.getElementById('search-meta');

    if (!sellers.length) {
        tbody.innerHTML = '<tr><td colspan="10" class="empty-msg">No se encontraron vendedores.</td></tr>';
        meta.textContent = 'Sin resultados';
        renderPagination(0, 1);
        return;
    }

    const start = (page - 1) * 50 + 1;
    const end   = Math.min(page * 50, total);
    meta.textContent = `Mostrando ${start}–${end} de ${total} vendedores`;

    tbody.innerHTML = sellers.map((s, i) => `
        <tr>
            <td style="color: var(--accent); font-weight:600">${s.seller_id}</td>
            <td>${s.name}</td>
            <td>${s.country}</td>
            <td>${s.city}</td>
            <td>${fmt.rating(s.rating)}</td>
            <td>${s.total_orders || 0}</td>
            <td>${fmt.currency(s.total_revenue)}</td>
            <td>${fmt.cancel(s.cancel_rate)}</td>
            <td>
                <span class="badge ${s.active ? 'badge-activo' : 'badge-inactivo'}">
                    ${s.active ? 'Activo' : 'Inactivo'}
                </span>
            </td>
            <td><button class="btn-detail" data-index="${i}">Ver detalle</button></td>
        </tr>
    `).join('');

    document.querySelectorAll('.btn-detail').forEach(btn => {
        btn.addEventListener('click', () => openDetail(currentSellers[parseInt(btn.dataset.index)]));
    });

    renderPagination(total, page);
}

function renderPagination(total, page) {
    const totalPages = Math.ceil(total / 50);
    const container  = document.getElementById('pagination');
    if (!container || totalPages <= 1) { if(container) container.innerHTML = ''; return; }

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
        btn.addEventListener('click', () => fetchSellers(parseInt(btn.dataset.page)));
    });
}

function openDetail(s) {
    document.getElementById('detail-seller-id').textContent  = s.seller_id;
    document.getElementById('detail-registro').textContent   = `Miembro desde: ${s.joined_date}`;

    const badge = document.getElementById('detail-activo-badge');
    badge.textContent = s.active ? 'Activo' : 'Inactivo';
    badge.className   = `badge ${s.active ? 'badge-activo' : 'badge-inactivo'}`;

    document.getElementById('d-nombre').textContent     = s.name;
    document.getElementById('d-email').textContent      = s.email;
    document.getElementById('d-telefono').textContent   = s.phone;
    document.getElementById('d-pais').textContent       = s.country;
    document.getElementById('d-ciudad').textContent     = s.city;
    document.getElementById('d-pedidos').textContent    = s.total_orders || 0;
    document.getElementById('d-ingresos').textContent   = fmt.currency(s.total_revenue);
    document.getElementById('d-cancelacion').innerHTML  = fmt.cancel(s.cancel_rate);
    document.getElementById('d-calificacion').innerHTML = fmt.rating(s.rating);
    document.getElementById('d-fecha').textContent      = s.joined_date;

    document.getElementById('detail-overlay').classList.add('open');
}

function closeDetail() {
    document.getElementById('detail-overlay').classList.remove('open');
}

async function fetchSellers(page = 1) {
    const q = document.getElementById('search-input').value.trim();
    const params = new URLSearchParams();
    if (q) params.append('q', q);
    params.append('page',  page);
    params.append('limit', 50);

    try {
        const res  = await fetch(`/api/sellers/?${params}`);
        const json = await res.json();
        renderTable(json.data, json.total, json.page);
    } catch {
        document.getElementById('sellers-tbody').innerHTML =
            '<tr><td colspan="10" class="empty-msg">Error al cargar los datos.</td></tr>';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    fetchKPIs();
    fetchSellers();

    document.getElementById('search-input').addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(fetchSellers, 300);
    });

    document.getElementById('detail-close').addEventListener('click', closeDetail);
    document.getElementById('detail-overlay').addEventListener('click', e => {
        if (e.target === document.getElementById('detail-overlay')) closeDetail();
    });
});