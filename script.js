
document.addEventListener("DOMContentLoaded", () => {
    const submitBtn = document.getElementById("submitBtn");

    if (submitBtn) {
        submitBtn.addEventListener("click", askQuestion);
    }
});

async function askQuestion() {
    const questionInput = document.getElementById("question").value.trim();
    const loading = document.getElementById("loading");
    const resultBox = document.getElementById("resultBox");
    const answerContent = document.getElementById("answerContent");

    if (!questionInput) {
        alert("Please enter a question!");
        return;
    }

    loading.style.display = "block";
    resultBox.style.display = "none";

    try {
        const response = await fetch("http://127.0.0.1:8000/rag/query", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                question: questionInput
            })
        });

        const data = await response.json();

        loading.style.display = "none";

        if (response.ok) {
            if (typeof data === "string") {
                answerContent.innerText = data;
            } else if (data.answer) {
                answerContent.innerText = data.answer;
            } else {
                answerContent.innerText = JSON.stringify(data, null, 2);
            }

            resultBox.style.display = "block";
        } else {
            alert("Error: " + (data.detail || "Failed to get answer"));
        }

    } catch (error) {
        loading.style.display = "none";
        console.error("Connection error:", error);
        alert("Server connection error! Make sure FastAPI is running on http://127.0.0.1:8000");
    }
}

