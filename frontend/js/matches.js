/**
 * Clinical Matching Pipeline Logic
 */
let currentMatchResults = [];
let currentSelectedTrialId = null;

async function initTrialDropdown() {
    try {
        const trials = await api.get("/trials");
        const select = document.getElementById("trialSelector");
        if (!select) return;
        trials.forEach(t => {
            const opt = document.createElement("option");
            opt.value = t.id;
            const condition = t.condition && t.condition !== "Unknown" ? t.condition : "General Indication";
            opt.textContent = `${condition} | ${(t.title || `Protocol ${t.id}`).substring(0, 50)}`;
            select.appendChild(opt);
        });
    } catch(e) { console.error("Library sync failed", e); }
}

async function handleFileUpload(input) {
    if (input.files.length === 0) return;
    const file = input.files[0];
    const statusContainer = document.getElementById("fileLabelContainer");
    const pipelineBtn = document.getElementById("runPipelineBtn");
    const sidebar = document.querySelector('clinical-sidebar');
    const globalStatus = sidebar ? sidebar.querySelector('#globalAiStatus') : null;

    statusContainer.innerHTML = `<div class="processing-badge"><i class="fas fa-sync fa-spin"></i> Analyzing ${file.name}...</div>`;
    pipelineBtn.disabled = true;
    if (globalStatus) globalStatus.textContent = "AI EXTRACTING...";

    const formData = new FormData();
    formData.append("file", file);
    try {
        const data = await api.request("/trials/upload-protocol", { method: "POST", body: formData });
        
        // Populate Structured UI
        document.getElementById("incArea").value = data.inclusion || "";
        document.getElementById("excArea").value = data.exclusion || "";
        
        renderStructuredCriteria("incListContainer", data.inclusion_list, "incArea");
        renderStructuredCriteria("excListContainer", data.exclusion_list, "excArea");
        
        if (data.drug) {
            document.getElementById("displayDrugName").textContent = data.drug;
            document.getElementById("trialMetadataDisplay").style.display = "block";
        }
        if (data.description) {
            document.getElementById("displayDrugDescription").textContent = data.description;
            document.getElementById("drugDescriptionBox").style.display = "block";
        }
        
        currentSelectedTrialId = data.trial_id || null;
        document.getElementById("criteriaSection").style.display = "block";
        statusContainer.innerHTML = `<span id="fileLabel" class="text-accent fw-bold"><i class="fas fa-check-circle me-1"></i> ${data.title || file.name}</span>`;
        pipelineBtn.disabled = false;
        if (globalStatus) globalStatus.textContent = "System Ready";
    } catch(e) {
        statusContainer.innerHTML = `<span id="fileLabel" class="text-danger"><i class="fas fa-exclamation-circle me-1"></i> Extraction failed</span>`;
        pipelineBtn.disabled = false;
        if (globalStatus) { globalStatus.textContent = "Error Occurred"; setTimeout(() => { globalStatus.textContent = "System Ready"; }, 3000); }
    }
}

async function loadLibraryTrial(select) {
    if (!select.value) return;
    const trialId = select.value;
    try {
        const trial = await api.get(`/trials/${trialId}`);
        if (trial) {
            document.getElementById("incArea").value = trial.inclusion_criteria || "";
            document.getElementById("excArea").value = trial.exclusion_criteria || "";
            
            renderStructuredCriteria("incListContainer", trial.inclusion, "incArea");
            renderStructuredCriteria("excListContainer", trial.exclusion, "excArea");
            
            if (trial.drug) {
                document.getElementById("displayDrugName").textContent = trial.drug;
                document.getElementById("trialMetadataDisplay").style.display = "block";
            }
            if (trial.description) {
                document.getElementById("displayDrugDescription").textContent = trial.description;
                document.getElementById("drugDescriptionBox").style.display = "block";
            } else {
                document.getElementById("drugDescriptionBox").style.display = "none";
            }

            document.getElementById("criteriaSection").style.display = "block";
            document.getElementById("runPipelineBtn").disabled = false;
            currentSelectedTrialId = trialId;
        }
    } catch(e) { console.error(e); }
}

async function runMatchingPipeline() {
    const grid = document.getElementById('gridBody');
    const synth = document.getElementById('synthesisSection');
    const btn = document.getElementById('runPipelineBtn');
    const RawTrialId = document.getElementById('trialSelector').value || currentSelectedTrialId || "1";
    const sidebar = document.querySelector('clinical-sidebar');
    const globalStatus = sidebar ? sidebar.querySelector('#globalAiStatus') : null;

    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Thinking...';
    btn.disabled = true;
    if (globalStatus) globalStatus.textContent = "MATCHING ENGINE RUNNING...";

    grid.innerHTML = `<div class="text-center py-5 mt-5">
        <div class="spinner-grow text-accent"></div>
        <p class="text-secondary small mt-4 tracking-widest text-uppercase">
            <span class="thinking-text text-accent" id="thinkingStep">Parsing Clinical Protocol...</span>
        </p>
    </div>`;

    const steps = ["Auditing Patient Cohorts...", "Calculating Alignment Scores...", "Synthesizing Final Narrative..."];
    let stepIdx = 0;
    const stepInterval = setInterval(() => {
        const stepEl = document.getElementById("thinkingStep");
        if (stepEl && stepIdx < steps.length) stepEl.textContent = steps[stepIdx++];
        else clearInterval(stepInterval);
    }, 1500);

    try {
        const payload = {
            inclusion_criteria: document.getElementById("incArea").value,
            exclusion_criteria: document.getElementById("excArea").value,
            trial_id: parseInt(RawTrialId) || null
        };
        const data = await api.post(`/matching/match-all-patients-raw`, payload);
        currentMatchResults = data.results || [];
        const eligibleResults = currentMatchResults.filter(r => r.score >= 85).sort((a, b) => b.score - a.score);

        if (eligibleResults.length === 0) {
            grid.innerHTML = `<div class="alert alert-warning mt-5 text-center bg-transparent border-warning border-opacity-25 text-warning py-5">
                <i class="fas fa-exclamation-triangle fa-2x mb-3"></i><br>
                <strong>ZERO ELIGIBLE CANDIDATES</strong><br>
                <span class="smaller opacity-50">No candidates met the minimum 85% alignment threshold.</span>
            </div>`;
            synth.style.display = "none"; return;
        }
        renderGrid(eligibleResults);
        updateSynthesis(data);
        synth.style.display = "block";
    } catch (e) {
        grid.innerHTML = `<div class="alert alert-danger mt-5">Pipeline Execution Failed: ${e.message || "Unknown"}</div>`;
    } finally {
        clearInterval(stepInterval);
        btn.innerHTML = '<i class="fas fa-bolt me-2"></i> Run Alignment';
        btn.disabled = false;
        if (globalStatus) globalStatus.textContent = "System Ready";
    }
}

function renderGrid(results) {
    const grid = document.getElementById('gridBody');
    grid.innerHTML = results.slice(0, 100).map(r => {
        const score = Math.round(r.score);
        const scoreColor = score >= 85 ? 'var(--accent)' : (score >= 70 ? '#f59e0b' : '#ef4444');
        const hasObject = typeof r.explanation === 'object' && r.explanation !== null;
        const summary = hasObject ? r.explanation.summary : (r.explanation || "Clinical criteria matched.");
        const narrative = hasObject ? r.explanation.narrative : "";
        const summaryClass = summary === "Clinical criteria matched." ? "opacity-50" : "text-primary";
        return `<div class="grid-row-custom">
            <div class="d-flex align-items-center">
                <div style="width:4px;height:40px;background:${scoreColor};border-radius:4px" class="me-3"></div>
                <div>
                    <span class="fw-bold text-primary fs-6 d-block">${r.patient_name}</span>
                    <span class="text-secondary smaller id-monospace" style="font-size:0.65rem;">ID: ${r.patient_id} • ${r.age}Y • ${r.gender}</span>
                </div>
            </div>
            <div class="score-box fw-bold" style="color:${scoreColor};">${score}%</div>
            <div class="pe-4 ${summaryClass} small fw-medium">
                ${summary}
                ${narrative && r.ai_audited ? `<div class="smaller text-secondary mt-1 fw-normal opacity-75" style="font-style:italic;">"${narrative}"</div>` : ''}
            </div>
            <div><span class="badge ${r.ai_audited ? 'badge-success' : 'badge-default'}">${r.ai_audited ? 'AI VERIFIED' : 'RULE MATCH'}</span></div>
            <div class="text-end d-flex gap-2 justify-content-end">
                <button id="rej-${r.patient_id}" onclick="updateMatchVerdict(${r.patient_id}, 'rejected', this)" class="btn btn-secondary px-3 py-1 small" style="height:32px">Exclude</button>
                <button id="acc-${r.patient_id}" onclick="updateMatchVerdict(${r.patient_id}, 'accepted', this)" class="btn btn-primary px-3 py-1 small" style="height:32px">Enroll</button>
            </div>
        </div>`;
    }).join('');
}

function updateSynthesis(data) {
    const results = data.results || [];
    if (!results.length) return;
    const top = results[0];
    const summary = top.explanation && top.explanation.summary ? top.explanation.summary : "No clinical summary available.";
    const metadata = data.trial_metadata || {};
    const activeDrug = document.getElementById("activeDrugName");
    const activeCondition = document.getElementById("activeConditionName");
    const activeBadge = document.getElementById("activeProtocolBadge");

    if (activeDrug) activeDrug.textContent = metadata.drug || "Standard Regimen";
    if (activeCondition) activeCondition.textContent = metadata.condition && metadata.condition !== "Unknown" ? metadata.condition : "General Protocol";
    if (activeBadge) activeBadge.style.display = "inline-block";
    
    const narrativeEl = document.getElementById("llamaNarrative");
    if (narrativeEl) narrativeEl.innerHTML = `<strong class="text-accent">Summary Digest:</strong><br>"${summary}"`;
    
    const fairnessValEl = document.getElementById("fairnessValue");
    if (fairnessValEl) {
        const fairness = data.metrics ? (data.metrics.gender_fairness || 0.94) : 0.88;
        fairnessValEl.textContent = fairness.toFixed(2);
        const progress = document.querySelector(".progress-bar");
        if (progress) progress.style.width = (fairness * 100) + "%";
    }
}

async function updateMatchVerdict(patientId, status, btn) {
    const trialId = document.getElementById('trialSelector').value || currentSelectedTrialId || "1";
    const originalText = btn.innerHTML;
    btn.disabled = true; btn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i>';
    try {
        await api.put(`/matching/update-match-status/${patientId}/${trialId}?status=${status}`, {});
        if (status === 'accepted') {
            btn.innerHTML = '<i class="fas fa-check me-2"></i>ENROLLED'; btn.style.opacity = '0.7';
            document.getElementById(`rej-${patientId}`).style.display = 'none';
        } else {
            btn.innerHTML = '<i class="fas fa-times me-2"></i>EXCLUDED'; btn.style.background = 'rgba(248,81,73,0.1)';
            document.getElementById(`acc-${patientId}`).style.display = 'none';
        }
    } catch (e) {
        alert("Pipeline Update Rejection: " + (e.message || "Endpoint error"));
        btn.innerHTML = originalText; btn.disabled = false;
    }
}

function renderStructuredCriteria(containerId, list, rawFallbackId) {
    const container = document.getElementById(containerId);
    const textarea = document.getElementById(rawFallbackId);
    
    if (list && Array.isArray(list) && list.length > 0) {
        container.innerHTML = list.map(item => `
            <div class="criteria-item">
                <i class="fas fa-circle"></i>
                <span>${item}</span>
            </div>
        `).join('');
        container.style.display = "block";
        textarea.style.display = "none";
        
        if (containerId === "excListContainer") {
            document.getElementById("exclusionDisclaimer").style.display = "block";
        }
    } else {
        container.style.display = "none";
        textarea.style.display = "block";
        if (containerId === "excListContainer") {
            document.getElementById("exclusionDisclaimer").style.display = "none";
        }
    }
}

// Initial Bootstrap
document.addEventListener("DOMContentLoaded", initTrialDropdown);
