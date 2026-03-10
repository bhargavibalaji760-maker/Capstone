/**
 * Clinical Identity & Profile Management
 */
function initProfile() {
    const user = JSON.parse(localStorage.getItem("user") || "{}");
    if (!user.email) return;

    const initials = (user.full_name || user.email || "U").split(" ").map(w => w[0]).join("").toUpperCase().slice(0, 2);

    document.getElementById("avatarInitials").textContent = initials;
    document.getElementById("userNameDisplay").textContent = user.full_name || user.email;
    document.getElementById("userEmailDisplay").textContent = user.email;
    document.getElementById("fullName").value = user.full_name || "";
    document.getElementById("institution").value = user.institution || "";
    document.getElementById("specialty").value = user.specialty || "General Research";

    // Re-init MDB inputs for value presence
    setTimeout(() => {
        document.querySelectorAll('.form-outline').forEach(el => {
            if (window.mdb && mdb.Input) new mdb.Input(el).init();
        });
    }, 100);

    document.getElementById("profileForm")?.addEventListener("submit", async (e) => {
        e.preventDefault();
        const updatedUser = {
            ...user,
            full_name: document.getElementById("fullName").value,
            institution: document.getElementById("institution").value,
            specialty: document.getElementById("specialty").value
        };
        localStorage.setItem("user", JSON.stringify(updatedUser));
        
        // UI Updates
        document.getElementById("userNameDisplay").textContent = updatedUser.full_name;
        const newInitials = updatedUser.full_name.split(" ").map(w => w[0]).join("").toUpperCase().slice(0, 2);
        document.getElementById("avatarInitials").textContent = newInitials;
        
        const msg = document.getElementById("saveMsg");
        if (msg) {
            msg.classList.remove("d-none");
            msg.scrollIntoView({ behavior: 'smooth', block: 'center' });
            setTimeout(() => msg.classList.add("d-none"), 5000);
        }
    });
}

// Initial Bootstrap
document.addEventListener("DOMContentLoaded", initProfile);
