/**
 * Dashboard Analytics & Live Data Feed
 */
async function loadDashboard() {
    try {
        const [patients, trials, stats] = await Promise.all([
            api.get("/patients"),
            api.get("/trials"),
            api.get("/dashboard/stats")
        ]);

        // Update Stat Cards
        document.getElementById("totalPatients").textContent = stats.total_patients || patients.length;
        document.getElementById("totalTrials").textContent = stats.total_trials || trials.length;
        document.getElementById("totalMatches").textContent = stats.total_matches || "0";
        document.getElementById("avgScore").textContent = (stats.avg_match_score || "0") + "%";

        // Render Recent Subjects
        const patientRows = patients.slice(0, 5).map(p => {
            const name = p.name && p.name !== 'null' ? p.name : 'Unknown Patient';
            const nameClass = name === 'Unknown Patient' ? 'data-placeholder' : 'data-primary';
            return `<tr>
                <td class="${nameClass}">${name}</td>
                <td class="text-secondary">${p.age || "--"}</td>
                <td><span class="badge bg-secondary bg-opacity-20 text-dim px-3">${(p.medical_history || "").split("|")[0] || "General"}</span></td>
            </tr>`;
        }).join("");
        document.getElementById("recentPatientsTable").innerHTML = patientRows || "<tr><td colspan='3' class='text-center text-muted py-3'>No recent subjects</td></tr>";

        // Render Recent Protocols
        const trialRows = trials.slice(0, 5).map(t => {
            const phaseColor = (t.phase || "").includes("III") ? "text-success" : ((t.phase || "").includes("II") ? "text-warning" : "text-info");
            return `<tr>
                <td class="text-truncate data-primary" style="max-width:250px;">${t.title}</td>
                <td><span class="badge bg-opacity-10 ${phaseColor} border border-white border-opacity-10 px-3">${t.phase || "N/A"}</span></td>
                <td><span class="badge bg-success bg-opacity-20 text-success px-3">Active</span></td>
            </tr>`;
        }).join("");
        document.getElementById("recentTrialsTable").innerHTML = trialRows || "<tr><td colspan='3' class='text-center text-muted py-3'>No active protocols</td></tr>";

    } catch (e) {
        console.error("Intelligence pipeline error:", e);
    }
}

// Initial Bootstrap
document.addEventListener("DOMContentLoaded", loadDashboard);
