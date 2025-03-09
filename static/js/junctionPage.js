// For the slider: highlight the active tick and update label.
const slider = document.getElementById("speedRange");
const speedLabel = document.getElementById("speedLabel");
const tickMarks = document.querySelectorAll("#rangeTicks span");

// Initial highlight
tickMarks.forEach(tick => {
  if (tick.textContent === slider.value) {
    tick.classList.add("activeTick");
  }
});

// On slider input
slider.addEventListener("input", () => {
  speedLabel.textContent = "Simulation Speed (" + slider.value + ")";
  tickMarks.forEach(tick => {
    tick.classList.toggle("activeTick", tick.textContent === slider.value);
  });
  // Send the updated simulation speed multiplier to the server
  ws.send(JSON.stringify({
    type: "speedUpdate",
    speed: parseFloat(slider.value)
  }));
});


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
    // Create a full-screen overlay that covers the entire page
    let overlay = document.createElement("div");
    overlay.id = "loadingOverlay";
    overlay.style.position = "fixed";
    overlay.style.top = "0";
    overlay.style.left = "0";
    overlay.style.width = "100vw";
    overlay.style.height = "100vh";
    overlay.style.backgroundColor = "#f8f5e9";  // Cream background
    overlay.style.display = "flex";
    overlay.style.flexDirection = "column";
    overlay.style.justifyContent = "center";
    overlay.style.alignItems = "center";
    overlay.style.zIndex = "9999";  // Ensure it's on top

    overlay.innerHTML = `
      <div style="text-align: center;">
        <div style="
            font-size: 4rem;
            animation: bounce 1s infinite;
          ">
          ⏳
        </div>
        <div style="
            font-size: 2rem;
            margin-bottom: 10px;
            color: #8da676;
          ">
          Processing results...
        </div>
        <div style="
            border: 8px solid #f3f3f3;
            border-top: 8px solid #8da676;
            border-radius: 50%;
            width: 60px;
            height: 60px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
          ">
        </div>
        <style>
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
          @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
          }
        </style>
      </div>
    `;

    // Append the overlay to the body
    document.body.appendChild(overlay);

    console.log("End button clicked. Stopping simulation...");

    try {
        if (window.ws) {
            console.log("🔌 Closing WebSocket connection...");
            window.ws.close();
        }

        // Fetch session_id and run_id
        let response = await fetch('/get_session_run_id');
        let data = await response.json();
        
        if (data.error) {
            console.error("Error fetching IDs:", data.error);
            return;
        }

        window.location.href = `/results?session_id=${data.session_id}&run_id=${data.run_id}`;

    } catch (error) {
        console.error("❌ Error sending stop request:", error);
    }
});
