document.addEventListener("DOMContentLoaded", () => {
    const chatBox = document.getElementById("chat-box");
    const userInput = document.getElementById("user-input");
    const sendBtn = document.getElementById("send-btn");
    const micBtn = document.getElementById("mic-btn");
    const langToggle = document.getElementById("lang-toggle");
    let currentLang = 'en'; // Default to English

    // Speech Recognition Setup
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition;
    
    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = true;
        // Language is set dynamically in the start() function
        
        recognition.onstart = function() {
            micBtn.style.color = 'var(--accent-color)';
            micBtn.classList.add('recording');
            userInput.placeholder = "Listening...";
        };
        
        recognition.onresult = function(event) {
            let final_transcript = '';
            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    final_transcript += event.results[i][0].transcript;
                }
            }
            if (final_transcript) {
               userInput.value += (userInput.value ? ' ' : '') + final_transcript;
               userInput.style.height = '';
               userInput.style.height = userInput.scrollHeight + 'px';
            }
        };
        
        recognition.onerror = function(event) {
            console.error("Speech recognition error", event.error);
            resetMic();
        };
        
        recognition.onend = function() {
            resetMic();
        };
    } else {
        console.warn("Speech Recognition API not supported in this browser.");
        if(micBtn) micBtn.style.display = "none";
    }

    function resetMic() {
        if(!micBtn) return;
        micBtn.style.color = 'var(--text-secondary)';
        micBtn.classList.remove('recording');
        userInput.placeholder = "Message Virtual Vita...";
    }

    if (micBtn) {
        micBtn.addEventListener("click", () => {
            if (SpeechRecognition) {
                if (micBtn.classList.contains('recording')) {
                    recognition.stop();
                } else {
                    // SET LANGUAGE DYNAMICALLY based on toggle
                    recognition.lang = (currentLang === 'te') ? 'te-IN' : 'en-US';
                    recognition.start();
                }
            }
        });
    }

    if (langToggle) {
        langToggle.addEventListener("click", () => {
            currentLang = (currentLang === 'en') ? 'te' : 'en';
            langToggle.innerText = currentLang.toUpperCase();
            langToggle.classList.toggle('active-te', currentLang === 'te');
            langToggle.title = `Switch Language (Current: ${currentLang.toUpperCase()})`;
        });
    }

    function addMessage(sender, text) {
        const messageDiv = document.createElement("div");
        messageDiv.className = `message ${sender === 'user' ? 'user' : 'bot'}`;
        
        const avatarDiv = document.createElement("div");
        avatarDiv.className = "avatar";
        avatarDiv.innerText = sender === 'user' ? 'U' : 'AI';
        
        const contentDiv = document.createElement("div");
        contentDiv.className = "message-content";
        
        // Parse markdown if marked is loaded
        if (typeof marked !== 'undefined') {
            contentDiv.innerHTML = marked.parse(text);
        } else {
            contentDiv.innerText = text;
        }

        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);
        
        chatBox.appendChild(messageDiv);
        chatBox.scrollTo({ top: chatBox.scrollHeight, behavior: 'smooth' });
    }

    function speakText(text) {
        if (!window.speechSynthesis) return;
        window.speechSynthesis.cancel();
        const cleanText = text.replace(/[*_#`]/g, '');
        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        
        // Dynamically detect if text contains Telugu script
        const isTelugu = /[\u0C00-\u0C7F]/.test(cleanText);
        utterance.lang = isTelugu ? 'te-IN' : 'en-US';
        
        window.speechSynthesis.speak(utterance);
    }

    async function handleSend() {
        const text = userInput.value.trim();
        if (!text) return;
        
        // Stop any ongoing speech when user sends a new message
        if (window.speechSynthesis) window.speechSynthesis.cancel();
        
        // Reset input
        userInput.value = "";
        userInput.style.height = '';
        sendBtn.disabled = true;

        // User message
        addMessage('user', text);

        // Add loading skeleton
        const loadingId = 'loading-' + Date.now();
        const loadingMessage = document.createElement('div');
        loadingMessage.className = 'message bot';
        loadingMessage.id = loadingId;
        loadingMessage.innerHTML = `
            <div class="avatar">AI</div>
            <div class="message-content" style="display:flex; align-items:center; gap:5px;">
                <span style="font-size:24px; animation: blink 1.4s infinite both;">.</span>
                <span style="font-size:24px; animation: blink 1.4s infinite both; animation-delay: 0.2s;">.</span>
                <span style="font-size:24px; animation: blink 1.4s infinite both; animation-delay: 0.4s;">.</span>
                <style>@keyframes blink { 0% { opacity: 0.2; } 20% { opacity: 1; } 100% { opacity: 0.2; } }</style>
            </div>
        `;
        chatBox.appendChild(loadingMessage);
        chatBox.scrollTo({ top: chatBox.scrollHeight, behavior: 'smooth' });

        try {
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ message: text })
            });

            const data = await response.json();
            
            if (!response.ok) {
                if (response.status === 429) {
                   throw new Error("Virtual Vita is currently very busy (Rate Limit). Please wait 30 seconds and try again!");
                }
                throw new Error(data.error || "Failed to get response");
            } if (data.error) {
                addMessage('bot', `**Error:** ${data.error}`);
                speakText(`Error: ${data.error}`);
            } else {
                addMessage('bot', data.response);
                speakText(data.response);
                
                // Trigger PDF generation if intake is complete
                if (data.is_complete && data.summary_data) {
                    generateClinicalPDF(data.summary_data);
                }
            }
        } catch (error) {
            document.getElementById(loadingId).remove();
            let networkErr = "Network Error: Could not connect to the server.";
            addMessage('bot', `**${networkErr}**`);
            speakText(networkErr);
            console.error(error);
        } finally {
            sendBtn.disabled = false;
            userInput.focus();
        }
    }

    sendBtn.addEventListener("click", handleSend);
    userInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    });

    document.getElementById("new-chat-btn").addEventListener("click", () => {
        chatBox.innerHTML = `
        <div class="message bot">
            <div class="avatar">AI</div>
            <div class="message-content">
                Hello again! I am Virtual Vita, your Intake Nurse. Could you provide your Name, Age, Weight, and Phone number before we start?
            </div>
        </div>`;
    });

    function generateClinicalPDF(data) {
        // Create an official download button in the chat
        const btnId = 'pdf-btn-' + Date.now();
        const actionDiv = document.createElement("div");
        actionDiv.className = "message bot";
        actionDiv.innerHTML = `
            <div class="avatar" style="background:var(--accent-color);">📄</div>
            <div class="message-content" style="background: rgba(16, 163, 127, 0.1); border: 1px solid var(--accent-color);">
                <strong>Intake Complete</strong><br>
                Your clinical summary is ready. You can download it and give it to your doctor.<br><br>
                <button id="${btnId}" class="lang-btn active-te" style="width: 100%; border-radius: 4px; padding: 10px; font-size: 14px;">📥 Download Medical Report (PDF)</button>
            </div>
        `;
        chatBox.appendChild(actionDiv);
        chatBox.scrollTo({ top: chatBox.scrollHeight, behavior: 'smooth' });

        document.getElementById(btnId).addEventListener("click", () => {
             // Populate hidden template
            document.getElementById("report-date").innerText = new Date().toLocaleDateString();
            document.getElementById("report-id").innerText = "VV-" + Math.floor(Math.random() * 1000000);
            document.getElementById("report-name").innerText = data.patient_name || "N/A";
            document.getElementById("report-age").innerText = data.age || "N/A";
            document.getElementById("report-weight").innerText = data.weight || "N/A";
            document.getElementById("report-phone").innerText = data.phone || "N/A";
            document.getElementById("report-cc").innerText = data.chief_complaint || "N/A";
            document.getElementById("report-hpi").innerText = data.history_of_present_illness || "N/A";

            // Generate PDF using html2pdf
            const element = document.getElementById('medical-report-template');
            
            // Unhide temporarily for capture
            const container = document.getElementById('pdf-report-container');
            container.style.display = 'block';
            
            const opt = {
              margin:       0,
              filename:     `Clinical_Summary_${data.patient_name || 'Patient'}.pdf`,
              image:        { type: 'jpeg', quality: 0.98 },
              html2canvas:  { scale: 2 },
              jsPDF:        { unit: 'in', format: 'letter', orientation: 'portrait' }
            };
            
            html2pdf().set(opt).from(element).save().then(() => {
                // Hide again after generation
                container.style.display = 'none';
            });
        });
    }
});
