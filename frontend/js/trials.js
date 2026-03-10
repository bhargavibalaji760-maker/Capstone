/**
 * Clinical Trials Registry Management
 */
let allTrials = [];
let searchTimeout;

const filterTrials = () => {
    const searchValue = document.getElementById("trialSearch").value.trim();
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => { loadTrials(searchValue); }, 300);
};

const localFilter = () => {
    const status = document.getElementById("statusFilter").value;
    const sort = document.getElementById("phaseSort").value;
    let filtered = [...allTrials];
    if (status) filtered = filtered.filter(t => (t.status || "").toLowerCase() === status.toLowerCase());

    const phasePriority = { "Phase I": 1, "Phase II": 2, "Phase III": 3, "Phase IV": 4 };
    if (sort === "asc") filtered.sort((a, b) => (phasePriority[a.phase] || 99) - (phasePriority[b.phase] || 99));
    else if (sort === "desc") filtered.sort((a, b) => (phasePriority[b.phase] || 0) - (phasePriority[a.phase] || 0));
    else filtered.sort((a, b) => b.id - a.id);

    renderTrials(filtered);
};

function phaseBadge(phase) {
    const p = (phase || "").toUpperCase();
    if (p.includes("III")) return "bg-opacity-20 text-success";
    if (p.includes("II")) return "bg-opacity-20 text-warning";
    return "bg-opacity-20 text-info";
}

function statusBadge(status) {
    const s = (status || "").toLowerCase();
    if (s === "recruiting") return "bg-opacity-20 text-success";
    if (s === "active") return "bg-opacity-20 text-info";
    return "bg-opacity-20 text-dim";
}

function renderTrials(trials) {
    const tbody = document.getElementById("trialTableBody");
    if (!trials.length) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center py-5 text-muted"><i class="fas fa-flask fa-2x mb-3 d-block"></i> No clinical trials indexed</td></tr>';
        return;
    }
    tbody.innerHTML = trials.map(t => {
        const trialId = t.trial_id || 'LOCAL-' + t.id;
        const idClass = t.trial_id ? 'id-monospace' : 'id-monospace opacity-75';
        const condition = t.condition || "General Indication";
        const conditionClass = condition === "General Indication" ? "data-placeholder" : "text-secondary";
        return `<tr>
            <td class="ps-4 ${idClass}">${trialId}</td>
            <td class="data-primary">${t.title}</td>
            <td class="${conditionClass}">${condition}</td>
            <td class="text-center"><span class="badge ${phaseBadge(t.phase)} px-3">${t.phase || 'N/A'}</span></td>
            <td class="text-center"><span class="badge ${statusBadge(t.status)} px-3">${t.status || 'Active'}</span></td>
            <td class="pe-4 text-end">
                <button class="btn btn-link btn-sm text-accent p-0 me-3" onclick="viewTrial(${t.id})">
                    <i class="fas fa-eye"></i>
                </button>
                <button class="btn btn-link btn-sm text-danger p-0 h-auto" onclick="deleteTrial(${t.id})">
                    <i class="fas fa-trash-alt"></i>
                </button>
            </td>
        </tr>`;
    }).join("");
}

async function deleteTrial(id) {
    if (!confirm("Remove this protocol from registry?")) return;
    try {
        await api.delete("/trials/" + id);
        loadTrials();
    } catch (e) {
        alert("Registry deletion failed.");
    }
}

async function loadTrials(search = "") {
    try {
        const url = search ? `/trials?search=${encodeURIComponent(search)}` : "/trials?limit=10";
        allTrials = await api.get(url);
        localFilter();
        loadStats();
    } catch (e) {
        document.getElementById("trialTableBody").innerHTML = '<tr><td colspan="6" class="text-center py-5 text-danger"><i class="fas fa-server fa-2x mb-3 d-block"></i> Registry Pipeline Disconnected</td></tr>';
    }
}

async function loadStats() {
    try {
        const stats = await api.get("/dashboard/stats");
        const cards = document.querySelectorAll(".glass-card h2");
        if (cards.length >= 4) {
            cards[0].innerText = stats.total_trials.toLocaleString();
            cards[3].innerText = stats.total_matches.toLocaleString();
        }
    } catch (e) { console.error("Stats load failed", e); }
}

async function viewTrial(id) {
    try {
        const t = await api.get(`/trials/${id}`);
        document.getElementById("viewTrialTitle").textContent = t.title;
        document.getElementById("viewTrialCondition").textContent = t.condition || "No primary indication specified.";
        document.getElementById("viewTrialDrug").textContent = t.drug || "Standard Protocol";
        document.getElementById("viewTrialDesc").textContent = t.description || "No supplemental rationale provided.";

        renderStructuredCriteria("viewTrialInclusion", t.inclusion, t.inclusion_criteria);
        renderStructuredCriteria("viewTrialExclusion", t.exclusion, t.exclusion_criteria);

        const modal = new mdb.Modal(document.getElementById('viewTrialModal'));
        modal.show();
    } catch (e) { alert("Detailed view failed."); }
}

function renderStructuredCriteria(containerId, list, rawFallback) {
    const container = document.getElementById(containerId);
    if (list && Array.isArray(list) && list.length > 0) {
        container.innerHTML = list.map(item => `
            <div class="criteria-item">
                <i class="fas fa-circle"></i>
                <span>${item}</span>
            </div>
        `).join('');
        if (containerId === "viewTrialExclusion") {
            document.getElementById("viewExclusionDisclaimer").style.display = "block";
        }
    } else {
        container.innerHTML = `<div class="text-secondary opacity-50 small italic">${rawFallback || "No criteria defined."}</div>`;
        if (containerId === "viewTrialExclusion") {
            document.getElementById("viewExclusionDisclaimer").style.display = "none";
        }
    }
}

// Initial Bootstrap
document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("trialSearch")?.addEventListener("input", filterTrials);
    document.getElementById("statusFilter")?.addEventListener("change", localFilter);
    document.getElementById("phaseSort")?.addEventListener("change", localFilter);

    // ── PDF Upload Wiring ───────────────────────────────────────────────
    const pdfInput = document.getElementById("pdfUploadInput");
    const pdfBtn = document.getElementById("pdfUploadBtn");
    const pdfName = document.getElementById("pdfFileName");
    const pdfStatus = document.getElementById("pdfUploadStatus");
    const pdfSuccess = document.getElementById("pdfUploadSuccess");
    const pdfError = document.getElementById("pdfUploadError");

    if (pdfInput) {
        pdfInput.addEventListener("change", () => {
            const file = pdfInput.files[0];
            if (file) {
                pdfName.textContent = file.name;
                pdfBtn.disabled = false;
            } else {
                pdfName.textContent = "No file selected";
                pdfBtn.disabled = true;
            }
            // Reset status
            pdfStatus.style.display = "none";
            pdfSuccess.style.display = "none";
            pdfError.style.display = "none";
            pdfError.textContent = "";
        });
    }

    if (pdfBtn) {
        pdfBtn.addEventListener("click", async () => {
            const file = pdfInput.files[0];
            if (!file) return;

            // Show progress
            pdfStatus.style.display = "block";
            pdfSuccess.style.display = "none";
            pdfError.style.display = "none";
            pdfError.textContent = "";
            pdfBtn.disabled = true;

            const formData = new FormData();
            formData.append("file", file);

            try {
                // Use api.request so the auth header is injected automatically
                const result = await api.request("/trials/upload-protocol", {
                    method: "POST",
                    body: formData   // FormData — api.js skips Content-Type header for FormData
                });

                if (!result) throw new Error("Upload returned empty response.");

                // Auto-populate form fields
                const setVal = (id, val) => {
                    const el = document.getElementById(id);
                    if (el && val !== undefined && val !== null) el.value = val;
                };

                setVal("trial_title", result.title || file.name.replace(".pdf", ""));
                setVal("trial_condition", result.condition || "");
                setVal("trial_inclusion", result.inclusion || "");
                setVal("trial_exclusion", result.exclusion || "");
                setVal("trial_min_age", result.min_age ?? 18);
                setVal("trial_max_age", result.max_age ?? 80);

                // Also try to fill description with drug info if present
                if (result.description) {
                    setVal("trial_desc", result.description);
                }

                // Trigger MDB re-init if available (so labels float correctly)
                if (typeof mdb !== 'undefined') {
                    document.querySelectorAll(".form-outline").forEach(el => {
                        try { new mdb.Input(el).update(); } catch (_) { }
                    });
                }

                pdfStatus.style.display = "none";
                pdfSuccess.style.display = "block";

            } catch (err) {
                console.error("PDF upload failed:", err);
                pdfStatus.style.display = "none";
                pdfError.style.display = "block";
                pdfError.textContent = "⚠ Extraction failed: " + (err.detail || err.message || "Unknown error. Check server logs.");
            } finally {
                pdfBtn.disabled = false;
            }
        });
    }

    // Reset PDF state when modal closes
    document.getElementById("addTrialModal")?.addEventListener("hidden.mdb.modal", () => {
        if (pdfInput) pdfInput.value = "";
        if (pdfName) pdfName.textContent = "No file selected";
        if (pdfBtn) pdfBtn.disabled = true;
        if (pdfStatus) pdfStatus.style.display = "none";
        if (pdfSuccess) pdfSuccess.style.display = "none";
        if (pdfError) { pdfError.style.display = "none"; pdfError.textContent = ""; }
    });

    // ── Manual Trial Form ───────────────────────────────────────────────
    document.getElementById("addTrialForm")?.addEventListener("submit", async (e) => {
        e.preventDefault();
        const payload = {
            title: document.getElementById("trial_title").value,
            condition: document.getElementById("trial_condition").value,
            description: document.getElementById("trial_desc").value,
            inclusion_criteria: document.getElementById("trial_inclusion").value,
            exclusion_criteria: document.getElementById("trial_exclusion").value,
            min_age: parseInt(document.getElementById("trial_min_age").value) || 18,
            max_age: parseInt(document.getElementById("trial_max_age").value) || 80,
            phase: document.getElementById("trial_phase").value,
            status: document.getElementById("trial_status").value
        };
        try {
            await api.post("/trials", payload);
            const modal = document.getElementById('addTrialModal');
            if (modal) {
                const modalInstance = mdb.Modal.getInstance(modal) || new mdb.Modal(modal);
                modalInstance.hide();
            }
            document.getElementById("addTrialForm").reset();
            loadTrials();
        } catch (err) {
            alert("Error: " + (err.detail || "Failed to save trial."));
        }
    });

    loadTrials();
});
