async function sendMessage() {

    let selected = [];

    document.querySelectorAll("#symptoms input:checked")
    .forEach(el => selected.push(el.value));

    if (selected.length === 0) {
        alert("Please select at least one symptom");
        return;
    }

    addMessage("You", selected.join(", "));

    try {
        const response = await fetch("http://127.0.0.1:8000/predict", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                symptoms: selected
            })
        });

        const data = await response.json();

        const botReply = `
🩺 Disease: ${data.disease}<br>
👨‍⚕️ Doctor: ${data.doctor}<br>
⚠️ Risk: ${data.risk_level}<br>
💊 Treatment: ${data.treatment}
        `;

        addMessage("AI Doctor", botReply);

    } catch (error) {
        addMessage("AI Doctor", "Error connecting to backend");
    }
}

function addMessage(sender, text) {
    const chatBox = document.getElementById("chat-box");

    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message");

    if (sender === "You") {
        messageDiv.classList.add("user");
    } else {
        messageDiv.classList.add("bot");
    }

    messageDiv.innerHTML = `<strong>${sender}:</strong><br>${text}`;

    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}