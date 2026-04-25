document.addEventListener("DOMContentLoaded", () => {
    fetchPatients();
    
    // Refresh data every 10 seconds
    setInterval(fetchPatients, 10000);
});

async function fetchPatients() {
    try {
        const response = await fetch('/api/patients');
        const patients = await response.json();
        
        updateDashboard(patients);
    } catch (e) {
        console.error("Failed to fetch patients", e);
    }
}

function updateDashboard(patients) {
    // Sort patients by logic: Critical > High > Medium > Low
    const severityMap = { "Critical": 4, "High": 3, "Medium": 2, "Low": 1, "N/A": 0 };
    
    patients.sort((a, b) => {
        const sevA = severityMap[a.triage_level] || 0;
        const sevB = severityMap[b.triage_level] || 0;
        return sevB - sevA; // Descending
    });

    const tbody = document.querySelector("#patient-table tbody");
    tbody.innerHTML = '';
    
    let highCount = 0;
    
    patients.forEach(p => {
        const tr = document.createElement("tr");
        
        let badgeClass = 'bg-low';
        let level = p.triage_level ? p.triage_level.toLowerCase() : '';
        if (level === 'critical' || level === 'high') {
            badgeClass = 'bg-high';
            highCount++;
        } else if (level === 'medium') {
            badgeClass = 'bg-medium';
        }
        
        tr.innerHTML = `
            <td style="font-family: monospace; color: var(--text-secondary);">${p.id || 'N/A'}</td>
            <td style="font-weight: 500;">${p.patient_name || 'N/A'}</td>
            <td>${p.age || 'N/A'}</td>
            <td style="max-width: 250px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${p.chief_complaint || 'N/A'}</td>
            <td><span class="badge ${badgeClass}">${p.triage_level || 'Pending'}</span></td>
            <td><button class="btn-view" onclick="generatePDF('${btoa(unescape(encodeURIComponent(JSON.stringify(p))))}')">View PDF Note</button></td>
        `;
        tbody.appendChild(tr);
    });
    
    // Update Stats
    document.getElementById("total-patients").innerText = patients.length;
    document.getElementById("high-priority").innerText = highCount;
    document.getElementById("waiting-patients").innerText = patients.filter(p => p.status === 'Waiting').length;
}

window.generatePDF = function(encodedData) {
    const data = JSON.parse(decodeURIComponent(escape(atob(encodedData))));
    
    document.getElementById("report-date").innerText = new Date(data.timestamp || Date.now()).toLocaleDateString();
    document.getElementById("report-id").innerText = data.id || "N/A";
    document.getElementById("report-name").innerText = data.patient_name || "N/A";
    document.getElementById("report-age").innerText = data.age || "N/A";
    document.getElementById("report-weight").innerText = data.weight || "N/A";
    document.getElementById("report-phone").innerText = data.phone || "N/A";
    document.getElementById("report-cc").innerText = data.chief_complaint || "N/A";
    document.getElementById("report-hpi").innerText = data.history_of_present_illness || "N/A";

    const element = document.getElementById('medical-report-template');
    const container = document.getElementById('pdf-report-container');
    container.style.display = 'block';
    
    const opt = {
      margin:       0,
      filename:     `SOAP_NOTE_${data.patient_name || 'Patient'}.pdf`,
      image:        { type: 'jpeg', quality: 0.98 },
      html2canvas:  { scale: 2 },
      jsPDF:        { unit: 'in', format: 'letter', orientation: 'portrait' }
    };
    
    html2pdf().set(opt).from(element).save().then(() => {
        container.style.display = 'none';
        alert("PDF Downloaded successfully for " + data.patient_name);
    });
};
