async function processAndDownloadPDF() {
    let url = document.getElementById("url").value;
    let language = document.getElementById("language").value;
    let loading = document.getElementById("loading");
    let generateBtn = document.getElementById("generate-btn");
    let downloadLink = document.getElementById("download-link");

    if (!url) {
        alert("Please enter a YouTube URL.");
        return;
    }

    // Show loading animation and disable the button
    loading.style.display = "flex";
    generateBtn.innerText = "Generating...";
    generateBtn.disabled = true;
    downloadLink.style.display = "none"; // Hide download button initially

    try {
        // Step 1: Fetch transcript
        let response = await fetch("/get_transcript", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url: url, language: language })
        });
        let transcriptData = await response.json();
        if (!response.ok) {
            throw new Error(transcriptData.error);
        }

        // Step 2: Generate summary
        let summaryResponse = await fetch("/generate_summary", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ transcript: transcriptData.transcript, language: language })
        });
        let summaryData = await summaryResponse.json();
        if (!summaryResponse.ok) {
            throw new Error(summaryData.error);
        }

        // Step 3: Save as PDF
        let saveResponse = await fetch("/save_summary", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ summary: summaryData.summary })
        });
        let saveData = await saveResponse.json();
        if (!saveResponse.ok) {
            throw new Error(saveData.error || "Failed to save PDF");
        }

        // Show the download button
        downloadLink.href = "/download_summary";
        downloadLink.style.display = "block";

        alert("✅ PDF is ready! Click the 'Download PDF' button below.");
    } catch (error) {
        alert("Error: " + error.message);
    } finally {
        // Hide loading animation , HIDE GENERATE PDF BUTTON, AND ENABLE DOWNLOAD PDF BUTTON
        loading.style.display = "none";
        generateBtn.hidden = true;
    }
}
