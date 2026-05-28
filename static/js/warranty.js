// warranty.js  — loads real data from sessionStorage or API

// ─────────────────────────────────────────────
//  HELPERS
// ─────────────────────────────────────────────
async function getBaseURL() {
    try {
        const res    = await fetch("../static/js/ip.json");
        const config = await res.json();
        return config.ip;
    } catch {
        return "";   // same-origin fallback
    }
}

function formatDate(isoStr) {
    if (!isoStr) return "—";
    const d = new Date(isoStr);
    const dd  = String(d.getDate()).padStart(2, "0");
    const mm  = String(d.getMonth() + 1).padStart(2, "0");
    const yyyy = d.getFullYear();
    return `${dd}-${mm}-${yyyy}`;
}

/** Returns { daysLeft, percent, status } */
function calcWarranty(purchaseDateStr, expiryDateStr) {
    const today   = new Date();
    today.setHours(0, 0, 0, 0);

    const purchase = new Date(purchaseDateStr);
    const expiry   = new Date(expiryDateStr);

    const totalDays = Math.round((expiry - purchase) / 86_400_000);
    const usedDays  = Math.round((today   - purchase) / 86_400_000);
    const daysLeft  = Math.max(0, totalDays - usedDays);
    const percent   = Math.min(100, Math.round((usedDays / totalDays) * 100));

    return {
        daysLeft,
        percent,
        status: daysLeft > 0 ? "active" : "expired"
    };
}

// ─────────────────────────────────────────────
//  FILL THE PAGE
// ─────────────────────────────────────────────
function populatePage(data) {
    // basic info

     // ADD THESE 2 LINES 👇
    console.log("=== WARRANTY DATA ===", data);
    console.table(data);

    setText("w_product_name",    data.product_name    || "—");
    setText("w_customer_name",   data.customer_name   || "—");
    setText("w_serial_number",   data.serial_number   || "—");
    setText("w_mac_id",          data.mac_id          || "—");
    setText("w_model_number",    data.model_number    || "—");
    setText("w_purchase_date",   formatDate(data.purchase_date));
    setText("w_warranty_expiry", formatDate(data.warranty_expiry));

    // warranty bar
    const { daysLeft, percent, status } = calcWarranty(
        data.purchase_date, data.warranty_expiry
    );

    setText("w_days_left", `${daysLeft} day${daysLeft !== 1 ? "s" : ""} remaining`);

    const bar = document.getElementById("w_progress_bar");
    if (bar) {
        bar.style.width = `${percent}%`;
        bar.classList.remove("bar-active", "bar-expired");
        bar.classList.add(status === "active" ? "bar-active" : "bar-expired");
    }

    const badge = document.getElementById("w_status_badge");
    if (badge) {
        badge.textContent = status === "active" ? "✔ Active" : "✖ Expired";
        badge.classList.remove("badge-active", "badge-expired");
        badge.classList.add(status === "active" ? "badge-active" : "badge-expired");
    }
}

function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
}

// ─────────────────────────────────────────────
//  MAIN — try sessionStorage first, else API
// ─────────────────────────────────────────────
async function loadWarranty() {
    // 1. Check sessionStorage (set by scanner.js after registration)
    const stored = sessionStorage.getItem("warrantyData");
    if (stored) {
        try {
            const data = JSON.parse(stored);
            populatePage(data);
            sessionStorage.removeItem("warrantyData");  // clean up
            return;
        } catch { /* fall through to API */ }
    }

    // 2. Fall back: read serial from URL and call API
    const params = new URLSearchParams(window.location.search);
    const serial = params.get("serial");

    if (!serial) {
        showError("No product information found. Please scan again.");
        return;
    }

    try {
        const BASE_URL = await getBaseURL();
        const res      = await fetch(`${BASE_URL}/warranty/${encodeURIComponent(serial)}`);
        const data     = await res.json();

        if (!res.ok) {
            showError(data.message || data.error || "Warranty not found.");
            return;
        }

        populatePage(data);

    } catch (err) {
        console.error(err);
        showError("Could not load warranty data. Please try again.");
    }
}

function showError(msg) {
    const container = document.getElementById("w_main_content");
    if (container) {
        container.innerHTML = `
            <div class="w_error_box">
                <p>⚠️ ${msg}</p>
                <button onclick="history.back()" class="warrenty_btn_submit" style="margin-top:16px">
                    ← Go Back
                </button>
            </div>`;
    }
}

// ─────────────────────────────────────────────
//  Back arrow
// ─────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
    loadWarranty();

    const backBtn = document.querySelector(".warrenty_back_arrow");
    if (backBtn) {
        backBtn.style.cursor = "pointer";
        backBtn.addEventListener("click", () => history.back());
    }
});