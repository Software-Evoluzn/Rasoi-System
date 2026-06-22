// scanner.js — updated
let scanDeviceId = "";
let scannedProduct = {};

const html5QrCode = new Html5Qrcode("reader");

async function getBaseURL() {
    const response = await fetch("../static/js/ip.json");
    const config   = await response.json();
    return config.ip;
}

// ✅ Page load pe logged in user check karo
document.addEventListener("DOMContentLoaded", function () {
    const userRaw = sessionStorage.getItem("loggedInUser");

    if (!userRaw) {
        alert("Please login first");
        window.location.href = "/";  // login page pe bhejo
        return;
    }

    const user = JSON.parse(userRaw);

    // UI mein naam dikhao (optional)
    const nameEl = document.getElementById("scanner_customer_name");
    const mobEl  = document.getElementById("scanner_customer_mobile");

    if (nameEl) nameEl.value = user.name   || "";
    if (mobEl)  mobEl.value  = user.mobile || "";

    console.log("[SCANNER] Logged in user:", user);
});

async function onScanSuccess(decodedText) {
    scanDeviceId = decodedText.trim();
    console.log("Scanned Device ID:", scanDeviceId);
    html5QrCode.stop();

    try {
        const BASE_URL = await getBaseURL();
        const response = await fetch(`${BASE_URL}/product/${scanDeviceId}`);
        const data     = await response.json();

        if (!response.ok) {
            alert(data.error || "Product not found");
            return;
        }

        scannedProduct = data;

        document.getElementById("serial_number").innerText = data.serial_number || "-";
        document.getElementById("model_name").innerText    = data.model_number  || "-";
        document.getElementById("mac_id").innerText        = data.mac_id        || "-";

        if (data.isRegistered) {
            alert("⚠️ This product is already registered.");
        }

    } catch (error) {
        console.error(error);
        alert("Server Error while fetching product");
    }
}

document.querySelector(".scanner_open_btn")
    .addEventListener("click", async function () {
        try {
            await html5QrCode.start(
                { facingMode: "environment" },
                { fps: 10, qrbox: { width: 250, height: 250 } },
                onScanSuccess
            );
        } catch (err) {
            console.error(err);
            alert(err);
        }
    });

document.querySelector(".scanner_link_btn")
    .addEventListener("click", async function () {

        const purchase_date = document.getElementById("scanner_purchase_date").value;

        // ✅ sessionStorage se user lo
        const userRaw = sessionStorage.getItem("loggedInUser");
        if (!userRaw) {
            alert("Session expired. Please login again.");
            window.location.href = "/";
            return;
        }

        const user            = JSON.parse(userRaw);
        const customer_name   = user.name   || "";
        const customer_mobile = user.mobile || "";

        if (!scanDeviceId) {
            alert("Please scan a product first");
            return;
        }

        if (!customer_name) {
            alert("Customer name not found. Please login again.");
            window.location.href = "/";
            return;
        }

        if (!purchase_date) {
            alert("Please select a purchase date");
            return;
        }

        try {
            const BASE_URL = await getBaseURL();

            const response = await fetch(`${BASE_URL}/register-product`, {
                method : "POST",
                headers: { "Content-Type": "application/json" },
                body   : JSON.stringify({
                    device_id       : scanDeviceId,
                    purchase_date   : purchase_date,
                    customer_name   : customer_name,    // ✅ login se aa raha
                    customer_mobile : customer_mobile   // ✅ login se aa raha
                })
            });

            const data = await response.json();
            console.log(data);

            if (!response.ok) {
                alert(data.error || "Registration failed");
                return;
            }

            const serial = data.serial_number || scannedProduct.serial_number || "";

            sessionStorage.setItem("warrantyData", JSON.stringify({
                product_name   : data.product_name,
                serial_number  : data.serial_number,
                model_number   : data.model_number,
                mac_id         : data.mac_id,
                customer_name  : data.customer_name,
                customer_mobile: data.customer_mobile,
                purchase_date  : data.purchase_date,
                warranty_expiry: data.warranty_expiry,
                warranty_years : data.warranty_years,
            }));

            // window.location.href = `/warranty-page?serial=${encodeURIComponent(serial)}`;
            window.location.href = `/dashboard_page`;

        } catch (error) {
            console.error(error);
            alert("Server Error");
        }
    });