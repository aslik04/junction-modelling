document.getElementById("backBtn").addEventListener("click", async () => {
    console.log("Back button clicked. Stopping FastAPI...");

    try {
        let stopResponse = await fetch('/stop_simulation', { method: 'POST' });
        let stopData = await stopResponse.json();
        
        if (stopResponse.ok) {
            console.log("✅ FastAPI stopped:", stopData.message);
            // Redirect back to the parameters page
            window.location.href = "/parameters";
        } else {
            console.error("❌ Error stopping FastAPI:", stopData.error);
        }
    } catch (error) {
        console.error("❌ Error sending stop request:", error);
    }
});

document.getElementById("endBtn").addEventListener("click", async () => {
    console.log("Back button clicked. Stopping FastAPI...");

    try {
        let stopResponse = await fetch('/stop_simulation', { method: 'POST' });
        let stopData = await stopResponse.json();
        
        if (stopResponse.ok) {
            console.log("✅ FastAPI stopped:", stopData.message);
            // Redirect back to the index page
            window.location.href = "/index";
        } else {
            console.error("❌ Error stopping FastAPI:", stopData.error);
        }
    } catch (error) {
        console.error("❌ Error sending stop request:", error);
    }
});


document.addEventListener('DOMContentLoaded', function() {
    const tutorialButton = document.getElementById('tutorial-button');
    const tutorialPopup = document.getElementById('tutorial-popup');
    const tutorialClose = document.getElementById('tutorial-close');
    
    tutorialButton.addEventListener('click', function() {
        tutorialPopup.style.display = 'block';
    });
    
    tutorialClose.addEventListener('click', function() {
        tutorialPopup.style.display = 'none';
    });
    
    // Close the popup when clicking outside of the content area
    tutorialPopup.addEventListener('click', function(e) {
        if(e.target === tutorialPopup) {
            tutorialPopup.style.display = 'none';
        }
    });
});