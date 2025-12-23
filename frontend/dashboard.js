async function loadDashboard() {
    try {
        const response = await fetch("https://ai-dropout-prediction-system.onrenderer.com/dashboard");
        const data = await response.json();

        document.getElementById("totalLogs").innerText = data.total_logs;

        // Risk distribution
        const riskList = document.getElementById("riskStats");
        riskList.innerHTML = "";
        for (const [risk, count] of Object.entries(data.risk_distribution)) {
            const li = document.createElement("li");
            li.innerText = `${risk}: ${count}`;
            riskList.appendChild(li);
        }

        // Interventions
        const interventionList = document.getElementById("interventionStats");
        interventionList.innerHTML = "";
        for (const [name, count] of Object.entries(data.intervention_distribution)) {
            const li = document.createElement("li");
            li.innerText = `${name}: ${count}`;
            interventionList.appendChild(li);
        }

        // Outcomes
        const outcomeList = document.getElementById("outcomeStats");
        outcomeList.innerHTML = "";
        for (const [outcome, count] of Object.entries(data.outcome_distribution)) {
            const li = document.createElement("li");
            li.innerText = `${outcome}: ${count}`;
            outcomeList.appendChild(li);
        }

    } catch (error) {
        alert("Failed to load dashboard data");
    }
}

loadDashboard();
