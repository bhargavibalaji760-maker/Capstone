/**
 * Clinical Records Repository Management
 */
let allPatients = [];
let searchTimeout;

const filterPatients = () => {
    const searchValue = document.getElementById("patientSearch").value.trim();
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => { loadPatients(searchValue); }, 300);
};

const localFilter = () => {
    const gender = document.getElementById("genderFilter")?.value;
    const sort = document.getElementById("ageSort")?.value;
    let filtered = [...allPatients];
    if (gender) filtered = filtered.filter(p => p.gender === gender);
    if (sort === "asc") filtered.sort((a, b) => (a.age || 0) - (b.age || 0));
    else if (sort === "desc") filtered.sort((a, b) => (b.age || 0) - (a.age || 0));
    else filtered.sort((a, b) => b.id - a.id);
    renderPatients(filtered);
};

function renderPatients(patients) {
    const tbody = document.getElementById("patientTableBody");
    if (!tbody) return;
    if (!patients.length) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center py-5 text-muted"><i class="fas fa-user-slash fa-2x mb-3 d-block"></i> No records found</td></tr>';
        return;
    }
    tbody.innerHTML = patients.map(p => {
        const name = p.name && p.name !== 'null' ? p.name : 'Unknown Patient';
        const nameClass = name === 'Unknown Patient' ? 'data-placeholder' : 'data-primary';
        let history = (p.medical_history || p.conditions || "--");
        if (history === 'nan') history = "--";
        const historyClass = history === '--' ? 'data-placeholder' : '';
        const cleanHistory = history.length > 80 ? history.substring(0, 80) + "..." : history;
        const age = p.age || 'N/A';
        const ageClass = age === 'N/A' ? 'data-placeholder' : 'text-secondary';
        return `<tr>
            <td class="ps-4 id-monospace">${p.subject_id}</td>
            <td class="${nameClass}">${name}</td>
            <td class="text-center ${ageClass}">${age}</td>
            <td class="text-center"><span class="badge bg-secondary bg-opacity-20 text-dim px-3">${p.gender === 'M' ? 'Male' : (p.gender === 'F' ? 'Female' : (p.gender || 'N/A'))}</span></td>
            <td class="text-secondary small ${historyClass}">${cleanHistory}</td>
        </tr>`;
    }).join('');
}

async function loadPatients(search = "") {
    try {
        const url = search ? `/patients?search=${encodeURIComponent(search)}` : "/patients?limit=10";
        allPatients = await api.get(url);
        localFilter();
        loadStats();
    } catch (e) {
        const tbody = document.getElementById("patientTableBody");
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center py-5 text-danger"><i class="fas fa-wifi-slash fa-2x mb-3 d-block"></i> Intelligence Pipeline Disconnected</td></tr>';
        }
    }
}

async function loadStats() {
    try {
        const stats = await api.get("/dashboard/stats");
        const totalElem = document.querySelector(".glass-card h2");
        if (totalElem) {
            totalElem.innerText = stats.total_patients.toLocaleString();
        }
    } catch (e) { console.error("Stats load failed", e); }
}

// Initial Bootstrap
document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("patientSearch")?.addEventListener("input", filterPatients);
    document.getElementById("genderFilter")?.addEventListener("change", localFilter);
    document.getElementById("ageSort")?.addEventListener("change", localFilter);

    document.getElementById("addPatientForm")?.addEventListener("submit", async (e) => {
        e.preventDefault();
        const hadmId = document.getElementById("hadm_id").value.trim();
        const payload = {
            subject_id: document.getElementById("subject_id").value,
            hadm_id: hadmId || null, // Convert empty string to null for Postgres unique index
            name: document.getElementById("patient_name").value,
            age: parseInt(document.getElementById("patient_age").value) || null,
            gender: document.getElementById("patient_gender").value,
            medical_history: document.getElementById("patient_treatments").value // Match backend schema field
        };
        try {
            await api.post("/patients", payload);
            const modal = document.getElementById('addPatientModal');
            if (modal) {
                const modalInstance = mdb.Modal.getInstance(modal) || new mdb.Modal(modal);
                modalInstance.hide();
            }
            document.getElementById("addPatientForm").reset();
            loadPatients();
        } catch (err) { 
            console.error("Registration Error:", err);
            alert("Error: " + (err.detail || "Failed to save patient. Check console for details.")); 
        }
    });

    loadPatients();
});
