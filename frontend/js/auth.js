/**
 * Authentication Flow (Login/Signup)
 */
const loginForm = document.getElementById("loginForm");
const signupForm = document.getElementById("signupForm");

function showError(elId, msg) {
    const el = document.getElementById(elId);
    if (el) {
        el.textContent = msg;
        el.classList.remove("d-none");
    }
}

if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;

        try {
            const data = await api.post("/auth/login", { email, password });
            if (data.access_token) {
                localStorage.setItem("access_token", data.access_token);
                localStorage.setItem("user", JSON.stringify(data.user));
                window.location.href = "/dashboard";
            }
        } catch (err) {
            showError("loginError", err.detail || "Invalid clinical credentials.");
        }
    });
}

if (signupForm) {
    signupForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const name = document.getElementById("full_name").value;
        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;

        try {
            await api.post("/auth/signup", { full_name: name, email, password });
            window.location.href = "/login";
        } catch (err) {
            showError("signupError", err.detail || "Clinical registration failed.");
        }
    });
}
