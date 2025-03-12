function fetchContent() {
    let url = document.getElementById("url").value;
    fetch("/get_transcript", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url })
    })
    .then(response => response.json())
    .then(data => {
        if (data.transcript) {
            document.getElementById("transcript").value = data.transcript;
        } else {
            alert(data.error);
        }
    })
    .catch(error => console.error("Error:", error));
}

function generateNotes() {
    let transcript = document.getElementById("transcript").value;
    fetch("/generate_summary", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ transcript: transcript })
    })
    .then(response => response.json())
    .then(data => {
        if (data.summary) {
            document.getElementById("summary").value = data.summary;
        } else {
            alert(data.error);
        }
    })
    .catch(error => console.error("Error:", error));
}

function saveNotes() {
    let summary = document.getElementById("summary").value;
    fetch("/save_summary", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ summary: summary })
    })
    .then(response => response.json())
    .then(data => {
        if (data.file) {
            document.getElementById("download-link").style.display = "block";
        }
        alert(data.message);
    })
    .catch(error => console.error("Error:", error));
}

document.getElementById('theme-toggle').addEventListener('click', function() {
    if (document.body.getAttribute('data-theme') === 'dark') {
        document.body.setAttribute('data-theme', 'light');
        this.textContent = 'Toggle Dark Mode';
    } else {
        document.body.setAttribute('data-theme', 'dark');
        this.textContent = 'Toggle Light Mode';
    }
});
