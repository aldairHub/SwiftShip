async function loadStats() {
  try {
    const [summaryRes, sellersRes] = await Promise.all([
      fetch("/api/orders/summary"),
      fetch("/api/sellers/summary"),
    ]);

    const summary = await summaryRes.json();
    const sellers = await sellersRes.json();

    document.getElementById("stat-orders").textContent  = "200,000+";
    document.getElementById("stat-countries").textContent = "12+";
    document.getElementById("stat-sellers").textContent = sellers.active.toLocaleString();
    document.getElementById("stat-revenue").textContent =
      "$" + (summary.total_revenue / 1_000_000).toFixed(1) + "M";
  } catch (e) {
    console.error("Error loading stats:", e);
  }
}

document.addEventListener("DOMContentLoaded", loadStats);