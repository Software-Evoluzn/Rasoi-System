function togglePass(id, btn) {
    const input = document.getElementById(id);
    const isPassword = input.type === "password";
    input.type = isPassword ? "text" : "password";

    btn.innerHTML = isPassword
        ? `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8
                         a18.45 18.45 0 0 1 5.06-5.94"/>
                <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8
                         a18.5 18.5 0 0 1-2.16 3.19"/>
                <line x1="1" y1="1" x2="23" y2="23"/>
           </svg>`
        : `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                <circle cx="12" cy="12" r="3"/>
           </svg>`;
}


document.getElementById("loginBtn").addEventListener("click", async function () {

    const email    = document.getElementById("email").value.trim();
    const password = document.getElementById("loginPassword").value;

    if (!email || !password) {
        alert("Please fill all fields");
        return;
    }

    try {
        const configResponse = await fetch("../static/js/ip.json");
        const config         = await configResponse.json();
        const BASE_URL       = config.ip;

        const response = await fetch(`${BASE_URL}/login`, {
            method : "POST",
            headers: { "Content-Type": "application/json" },
            body   : JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (response.ok) {

            // ✅ User info sessionStorage mein save karo
            sessionStorage.setItem("loggedInUser", JSON.stringify({
                name  : data.name,
                mobile: data.mobile,
                email : data.email
            }));

            console.log("[LOGIN] User saved to sessionStorage:", data.name);

            // Redirect
            window.location.href = "/product_scan";

        } else {
            alert(data.error);
        }

    } catch (error) {
        console.error(error);
        alert("Server Error");
    }

});