const form = document.getElementById("predictForm");
const resultDiv = document.getElementById("result");
const loadingDiv = document.getElementById("loading");
const submitBtn = document.getElementById("submitBtn");
const interventionSection = document.getElementById("interventionSection");
const logBtn = document.getElementById("logBtn");

let lastPrediction = null;

/* -----------------------------
   PREDICT RISK
----------------------------- */
form.addEventListener("submit", async function (e) {
    e.preventDefault();

    const data = {
        attendance: Number(attendance.value),
        internal_marks: Number(marks.value),
        quiz_score: Number(quiz.value),
        login_frequency: Number(login.value),
        financial_issue: Number(financial.value),
        backlog_count: Number(backlog.value)
    };

    resultDiv.style.display = "none";
    interventionSection.style.display = "none";
    loadingDiv.style.display = "block";
    submitBtn.disabled = true;

    try {
        const response = await fetch("http://127.0.0.1:8000/predict", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        let factorsHTML = "";
        result.top_risk_factors.forEach(f => {
            factorsHTML += `<li>${f}</li>`;
        });

        resultDiv.className = "result " + result.risk_level.toLowerCase();
        resultDiv.innerHTML = `
            <p><strong>Dropout Risk:</strong> ${result.dropout_risk_percentage}%</p>
            <p><strong>Risk Level:</strong> ${result.risk_level}</p>
            <p><strong>Top Risk Factors:</strong></p>
            <ul>${factorsHTML}</ul>
        `;

        resultDiv.style.display = "block";

        // ✅ STORE prediction for intervention logging
        lastPrediction = {
            ...data,
            risk_level: result.risk_level
        };

        // ✅ SHOW intervention section
        interventionSection.style.display = "block";

    } catch (err) {
        resultDiv.className = "result high-risk";
        resultDiv.innerHTML = "Error connecting to backend";
        resultDiv.style.display = "block";
    } finally {
        loadingDiv.style.display = "none";
        submitBtn.disabled = false;
    }
});

/* -----------------------------
   LOG INTERVENTION
----------------------------- */
logBtn.addEventListener("click", async function () {

    const intervention = document.getElementById("interventionSelect").value;

    if (!intervention) {
        alert("Please select an intervention");
        return;
    }

    const payload = {
        ...lastPrediction,
        intervention_taken: intervention
    };

    try {
        await fetch("http://127.0.0.1:8000/log-intervention", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        alert("Intervention logged successfully");

    } catch {
        alert("Failed to log intervention");
    }
});
