
    // Global flag to indicate that a file upload is being used
    let fileUploadUsed = false;
  
    document.addEventListener('DOMContentLoaded', function () {
      // Toggle logic for each drop-down (only one open at a time)
      const dropdowns = document.querySelectorAll('.dropdown-heading');
      dropdowns.forEach(heading => {
        heading.addEventListener('click', () => {
          const content = heading.nextElementSibling;
          // Close all other dropdowns
          dropdowns.forEach(other => {
            if (other !== heading) {
              const otherContent = other.nextElementSibling;
              otherContent.style.display = 'none';
              other.querySelector('.symbol').textContent = '—';
            }
          });
          // Toggle current dropdown
          if (content.style.display === 'block') {
            content.style.display = 'none';
            heading.querySelector('.symbol').textContent = '—';
          } else {
            content.style.display = 'block';
            heading.querySelector('.symbol').textContent = '|';
          }
        });
      });
  
      // Drag & Drop functionality for file upload area
      const dropZone = document.querySelector('.drag-drop-box');
      const fileInput = document.getElementById('file-input');
  
      // Function to automatically upload the file using fetch,
      // and redirect if a redirect_url is returned.
      function autoUploadFile() {
        if (fileInput.files.length) {
          // Set the flag to indicate we're using file data
          fileUploadUsed = true;

          // Step 3: Create a full-screen overlay that displays Building simulation logic.
          let overlay = document.createElement("div");
          overlay.id = "buildingSimOverlay";
          overlay.style.position = "fixed";
          overlay.style.top = "0";
          overlay.style.left = "0";
          overlay.style.width = "100vw";
          overlay.style.height = "100vh";
          overlay.style.backgroundColor = "#f8f5e9";
          overlay.style.display = "flex";
          overlay.style.flexDirection = "column";
          overlay.style.justifyContent = "center";
          overlay.style.alignItems = "center";
          overlay.style.zIndex = "9999"; // Ensure it covers everything
      
          overlay.innerHTML = `
            <div style="font-size: 4rem; animation: bounce 1s infinite;">🏗️</div>
            <div style="font-size: 2rem; margin-bottom: 10px; color: #8da676;">Building simulation...</div>
            <div style="border: 8px solid #f3f3f3; border-top: 8px solid #8da676; border-radius: 50%; width: 60px; height: 60px; animation: spin 1s linear infinite;"></div>
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
          `;

          document.body.appendChild(overlay);

          const formData = new FormData();
          // Append the first file (or loop if handling multiple files)
          formData.append('file', fileInput.files[0]);
          fetch('/upload', {
            method: 'POST',
            body: formData,
          })
          .then(response => response.json())
          .then(data => {
            console.log("File uploaded successfully:", data);
            // Overwrite the current lanes value with the lanes from the JSON response
            if(data.lanes !== undefined) {
              localStorage.setItem("numOfLanes", data.lanes);
              // Also update the lanes slider to reflect the returned value
              document.getElementById("lanes").value = data.lanes;
            }
            // Redirect as usual
            if(data.redirect_url) {
              window.location.href = data.redirect_url;
            }
          })
          .catch(error => {
            console.error("File upload error:", error);
          });
        }
      }
  
      dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.style.backgroundColor = '#ececec';
      });
      dropZone.addEventListener('dragleave', () => {
        dropZone.style.backgroundColor = '#f8f5e9';
      });
      dropZone.addEventListener('drop', (e) => {

        // Step 3: Create a full-screen overlay that displays Building simulation logic.
        let overlay = document.createElement("div");
        overlay.id = "buildingSimOverlay";
        overlay.style.position = "fixed";
        overlay.style.top = "0";
        overlay.style.left = "0";
        overlay.style.width = "100vw";
        overlay.style.height = "100vh";
        overlay.style.backgroundColor = "#f8f5e9";
        overlay.style.display = "flex";
        overlay.style.flexDirection = "column";
        overlay.style.justifyContent = "center";
        overlay.style.alignItems = "center";
        overlay.style.zIndex = "9999"; // Ensure it covers everything
    
        overlay.innerHTML = `
          <div style="font-size: 4rem; animation: bounce 1s infinite;">🏗️</div>
          <div style="font-size: 2rem; margin-bottom: 10px; color: #8da676;">Building simulation...</div>
          <div style="border: 8px solid #f3f3f3; border-top: 8px solid #8da676; border-radius: 50%; width: 60px; height: 60px; animation: spin 1s linear infinite;"></div>
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
        `;

        document.body.appendChild(overlay);

        e.preventDefault();
        dropZone.style.backgroundColor = '#f8f5e9';
        if (e.dataTransfer.files.length) {
          fileInput.files = e.dataTransfer.files;
          autoUploadFile(); // Automatically post the file after drop
        }
      });
      dropZone.addEventListener('click', () => {
        fileInput.click();
      });
      // Listen for file selection via file input (click) and auto-upload
      fileInput.addEventListener('change', autoUploadFile);
  
      // Toggle enable/disable for Traffic Light Settings inputs
      const tlCheckbox = document.getElementById('traffic-light-enable');
      const tlInputs = document.querySelectorAll('.traffic-light-settings input[type="number"]');
      tlCheckbox.addEventListener('change', () => {
        tlInputs.forEach(input => {
          input.disabled = !tlCheckbox.checked;
        });
      });
      // Set initial state for traffic light inputs
      tlInputs.forEach(input => {
        input.disabled = !tlCheckbox.checked;
      });
  
      // When the Start button is clicked, check if a file upload was used.
      // If not, copy the manual form values into the hidden form and submit it.
      document.getElementById("startButton").addEventListener("click", async function () {

        // Step 3: Create a full-screen overlay that displays Building simulation logic.
        let overlay = document.createElement("div");
        overlay.id = "buildingSimOverlay";
        overlay.style.position = "fixed";
        overlay.style.top = "0";
        overlay.style.left = "0";
        overlay.style.width = "100vw";
        overlay.style.height = "100vh";
        overlay.style.backgroundColor = "#f8f5e9";
        overlay.style.display = "flex";
        overlay.style.flexDirection = "column";
        overlay.style.justifyContent = "center";
        overlay.style.alignItems = "center";
        overlay.style.zIndex = "9999"; // Ensure it covers everything
    
        overlay.innerHTML = `
          <div style="font-size: 4rem; animation: bounce 1s infinite;">🏗️</div>
          <div style="font-size: 2rem; margin-bottom: 10px; color: #8da676;">Building simulation...</div>
          <div style="border: 8px solid #f3f3f3; border-top: 8px solid #8da676; border-radius: 50%; width: 60px; height: 60px; animation: spin 1s linear infinite;"></div>
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
        `;

        document.body.appendChild(overlay);

        // If a file upload was used, skip manual submission.
        if (fileUploadUsed) {
          console.log("File upload detected; using file data only. Manual parameters will be ignored.");
          return; // Do nothing – the file upload already handled submission.
        }
        try {
          // Step 1: Start FastAPI before submitting form
          let startResponse = await fetch('/start_simulation', { method: 'POST' });
          let startData = await startResponse.json();
  
          if (startResponse.ok) {
            console.log("FastAPI started:", startData.message);
  
            // Step 2: Copy form values to hidden fields (manual parameters)
            document.getElementById("hidden_nb_forward").value = document.getElementById("nb_forward").value;
            document.getElementById("hidden_nb_left").value = document.getElementById("nb_left").value;
            document.getElementById("hidden_nb_right").value = document.getElementById("nb_right").value;
  
            document.getElementById("hidden_eb_forward").value = document.getElementById("eb_forward").value;
            document.getElementById("hidden_eb_left").value = document.getElementById("eb_left").value;
            document.getElementById("hidden_eb_right").value = document.getElementById("eb_right").value;
  
            document.getElementById("hidden_sb_forward").value = document.getElementById("sb_forward").value;
            document.getElementById("hidden_sb_left").value = document.getElementById("sb_left").value;
            document.getElementById("hidden_sb_right").value = document.getElementById("sb_right").value;
  
            document.getElementById("hidden_wb_forward").value = document.getElementById("wb_forward").value;
            document.getElementById("hidden_wb_left").value = document.getElementById("wb_left").value;
            document.getElementById("hidden_wb_right").value = document.getElementById("wb_right").value;
  
            document.getElementById("hidden_lanes").value = document.getElementById("lanes").value;
            document.getElementById("hidden_pedestrian_frequency").value = document.getElementById("pedestrian-frequency").value;
            document.getElementById("hidden_pedestrian_duration").value = document.getElementById("pedestrian-duration").value;
  
            // Traffic Light Settings values
            document.getElementById("hidden_tl_enabled").value = tlCheckbox.checked ? "on" : "";
            document.getElementById("hidden_sequences").value = document.getElementById("tl_sequences").value;
            document.getElementById("hidden_vmain").value = document.getElementById("tl_vmain").value;
            document.getElementById("hidden_hmain").value = document.getElementById("tl_hmain").value;
            document.getElementById("hidden_vright").value = document.getElementById("tl_vright").value;
            document.getElementById("hidden_hright").value = document.getElementById("tl_hright").value;
  
            // Step 3: Submit the hidden form after FastAPI has started
            console.log("Submitting form with manual parameters...");
            document.getElementById("hiddenForm").submit();
          } else {
            console.error("Error starting FastAPI:", startData.error);
          }
        } catch (error) {
          console.error("Error sending start request:", error);
        }
      });
    });
    // This script listens for changes to the lanes slider and stores its value in local storage.
    document.addEventListener('DOMContentLoaded', function () {
      const lanesSlider = document.getElementById("lanes");
      localStorage.clear()
      lanesSlider.addEventListener("input", function() {
        localStorage.setItem("numOfLanes", this.value);
      });
    });
    document.addEventListener('DOMContentLoaded', function () {
      const pedestrianDurationInput = document.getElementById("pedestrian-duration");
      localStorage.clear()
      // Check if a value exists in localStorage
      const storedDuration = localStorage.getItem("pedestrianDuration");
      if (storedDuration !== null) {
        // Use the stored value if it exists
        pedestrianDurationInput.value = storedDuration;
      } else {
        // Otherwise, set a default value (e.g., "1") and store it
        pedestrianDurationInput.value = "1";
        localStorage.setItem("pedestrianDuration", "1");
      }
      // Update localStorage whenever the input changes
      pedestrianDurationInput.addEventListener("input", function() {
        localStorage.setItem("pedestrianDuration", this.value);
      });
    });
    // Function to compute sequence lengths (mirroring your Python function)
    function getSequenceLengths(vehicleData) {
      let main_vertical = 0, main_horizontal = 0, vertical_right = 0, horizontal_right = 0;
      const increment = 4;
      
      // Parse values and ensure numbers
      const north = vehicleData.north || {};
      const south = vehicleData.south || {};
      const east  = vehicleData.east  || {};
      const west  = vehicleData.west  || {};
    
      const vertical_total = (parseInt(north.forward) || 0) + (parseInt(north.left) || 0) +
                             (parseInt(south.forward) || 0) + (parseInt(south.left) || 0);
      const horizontal_total = (parseInt(east.forward) || 0) + (parseInt(east.left) || 0) +
                               (parseInt(west.forward) || 0) + (parseInt(west.left) || 0);
      const vertical_right_total = (parseInt(north.right) || 0) + (parseInt(south.right) || 0);
      const horizontal_right_total = (parseInt(east.right) || 0) + (parseInt(west.right) || 0);
      
      const total = vertical_total + horizontal_total + vertical_right_total + horizontal_right_total;
      
      if (total > 0) {
        const raw_main_vertical = 60 * (vertical_total / total);
        const raw_main_horizontal = 60 * (horizontal_total / total);
        const raw_vertical_right = 60 * (vertical_right_total / total);
        const raw_horizontal_right = 60 * (horizontal_right_total / total);
        
        main_vertical = Math.ceil(raw_main_vertical / increment);
        main_horizontal = Math.ceil(raw_main_horizontal / increment);
        vertical_right = Math.ceil(raw_vertical_right / increment);
        horizontal_right = Math.ceil(raw_horizontal_right / increment);
      }
      
      return { main_vertical, main_horizontal, vertical_right, horizontal_right };
    }
    
    // Function to compute cycle times (using 2-second transitions as in your Python code)
    function getCycleTimes(seqLengths) {
      const gap = 1;
      const verticalCycleTime = seqLengths.main_vertical + seqLengths.vertical_right;
      const horizontalCycleTime = seqLengths.main_horizontal + seqLengths.horizontal_right;
      return { verticalCycleTime, horizontalCycleTime };
    }
    
    // Function to compute maximum gaps per minute given a cycle gap time
    function getMaxGapsPerMinute(seqLengths, gap) {
      const cycleTimes = getCycleTimes(seqLengths);
      // Full cycle includes a vertical cycle + gap + horizontal cycle + gap.
      const fullCycleTime = cycleTimes.verticalCycleTime + cycleTimes.horizontalCycleTime;
      // Each full cycle yields 2 gaps.
      return 2 * (60 / fullCycleTime);
    }
    
    // Function to update calculations in real time
    function updateCalculations() {
      // Read current vehicle input values from the form
      const vehicleData = {
        north: {
          forward: document.getElementById('nb_forward').value,
          left: document.getElementById('nb_left').value,
          right: document.getElementById('nb_right').value
        },
        east: {
          forward: document.getElementById('eb_forward').value,
          left: document.getElementById('eb_left').value,
          right: document.getElementById('eb_right').value
        },
        south: {
          forward: document.getElementById('sb_forward').value,
          left: document.getElementById('sb_left').value,
          right: document.getElementById('sb_right').value
        },
        west: {
          forward: document.getElementById('wb_forward').value,
          left: document.getElementById('wb_left').value,
          right: document.getElementById('wb_right').value
        }
      };
    
      // Get sequence lengths based on current vehicle data
      const seqLengths = getSequenceLengths(vehicleData);
      // Define gap duration (in seconds) as needed
      const gap = document.getElementById('pedestrian-duration').value;
    
      // Calculate max pedestrian frequency (gaps per minute)
      const maxGaps = getMaxGapsPerMinute(seqLengths, gap);
    
      // Update the pedestrian frequency input's max attribute
      const pedInput = document.getElementById('pedestrian-frequency');
      pedInput.max = maxGaps;
    }
    
    // Attach the update function to all vehicle input fields so it runs on every change
    document.addEventListener('DOMContentLoaded', function () {
      const vehicleInputs = [
        'nb_forward', 'nb_left', 'nb_right',
        'eb_forward', 'eb_left', 'eb_right',
        'sb_forward', 'sb_left', 'sb_right',
        'wb_forward', 'wb_left', 'wb_right'
      ];
    
      vehicleInputs.forEach(function(id) {
        const inputField = document.getElementById(id);
        if (inputField) {
          inputField.addEventListener('input', updateCalculations);
        }
      });
    });

    document.addEventListener("DOMContentLoaded", function () {
    // List of input fields to restrict
    const inputIds = [
        "nb_forward", "nb_left", "nb_right",
        "eb_forward", "eb_left", "eb_right",
        "wb_forward", "wb_left", "wb_right",
        "sb_forward", "sb_left", "sb_right"
    ];

    inputIds.forEach(function (id) {
        const inputField = document.getElementById(id);
        if (inputField) {
            // Ensure valid values (0-1000) on input
            inputField.addEventListener("input", function () {
                let value = parseInt(this.value, 10);
                
                if (isNaN(value) || value < 0) {
                    this.value = 0;
                } else if (value > 1000) {
                    this.value = 1000;
                }
            });

            // Set default value to 0 if empty
            inputField.addEventListener("blur", function () {
                if (this.value.trim() === "") {
                    this.value = 0;
                }
            });
        }
    });
});


    // Replicate your Python calculations in JavaScript
    function updateAndValidateTrafficSettings() {
      // Retrieve the number of sequences and set gap duration
      let sequences = parseInt(document.getElementById("tl_sequences").value) || 1;
      let gap = 1;
      
      // Retrieve the current green time values
      let vmainInput = document.getElementById("tl_vmain");
      let vrightInput = document.getElementById("tl_vright");
      let hmainInput = document.getElementById("tl_hmain");
      let hrightInput = document.getElementById("tl_hright");
      
      let vmain = parseInt(vmainInput.value) || 0;
      let vright = parseInt(vrightInput.value) || 0;
      let hmain = parseInt(hmainInput.value) || 0;
      let hright = parseInt(hrightInput.value) || 0;
      
      // Calculate total vertical and horizontal values
      // Adding  as the fixed transition time component
      let vTotal = vmain + vright;
      let hTotal = hmain + hright;
      
      // Compute the maximum allowed totals for each direction
      let maxV = 60 - hTotal;
      let maxH = 60 - vTotal;
      
      // Validate vertical green times
      if (vTotal > maxV) {
        vright = Math.max(0, maxV - vmain);
        vrightInput.value = vright;
        console.log("Adjusted vertical_right_green to", vright, "to meet max allowed vertical sum of", maxV);
      }
      
      // Validate horizontal green times
      if (hTotal > maxH) {
        hright = Math.max(0, maxH - hmain);
        hrightInput.value = hright;
        console.log("Adjusted horizontal_right_green to", hright, "to meet max allowed horizontal sum of", maxH);
      }
      
      // Return the normalized values (dividing by number of sequences)
      return {
        vertical_main_green: vmain / sequences,
        vertical_right_green: vright / sequences,
        horizontal_main_green: hmain / sequences,
        horizontal_right_green: hright / sequences,
      };
    }
  
    // Attach event listeners to update limits and validate as the user types:
    document.addEventListener('DOMContentLoaded', function () {
      // When tl_sequences changes, update the limits and validate the green fields
      document.getElementById("tl_sequences").addEventListener('input', () => {
        updateAndValidateTrafficSettings();
      });
      // Also attach validation to the green fields
      const greenFields = ["tl_vmain", "tl_vright", "tl_hmain", "tl_hright"];
      greenFields.forEach(id => {
        document.getElementById(id).addEventListener('input', updateAndValidateTrafficSettings);
      });
    });
  
    // Compute cycle times (using 2-second transitions as in Python)
    function getCycleTimes(seqLengths, gap) {
      const verticalCycleTime = seqLengths.main_vertical + seqLengths.vertical_right + 5*gap;
      const horizontalCycleTime = seqLengths.main_horizontal + seqLengths.horizontal_right + 5*gap;
      return { verticalCycleTime, horizontalCycleTime };
    }
    
    // Calculate max gap opportunities per minute
    function getMaxGapsPerMinute(seqLengths, gap) {
      const cycleTimes = getCycleTimes(seqLengths, gap);
      const maxVerticalGaps = 60 / cycleTimes.verticalCycleTime;
      const maxHorizontalGaps = 60 / cycleTimes.horizontalCycleTime;
      return maxVerticalGaps + maxHorizontalGaps;
    }
    
    // This function reads the current vehicle data, calculates max gaps,
    // and updates the max attribute of the pedestrian frequency input.
    function updatePedestrianMax() {
      const vehicleData = {
        north: {
          forward: document.getElementById('nb_forward').value,
          left: document.getElementById('nb_left').value,
          right: document.getElementById('nb_right').value
        },
        east: {
          forward: document.getElementById('eb_forward').value,
          left: document.getElementById('eb_left').value,
          right: document.getElementById('eb_right').value
        },
        south: {
          forward: document.getElementById('sb_forward').value,
          left: document.getElementById('sb_left').value,
          right: document.getElementById('sb_right').value
        },
        west: {
          forward: document.getElementById('wb_forward').value,
          left: document.getElementById('wb_left').value,
          right: document.getElementById('wb_right').value
        }
      };
  
      let enabled = document.getElementById("traffic-light-enable").checked;
  
      let seqLengths;
      if (enabled) {
        seqLengths = updateAndValidateTrafficSettings();
      } else {
        seqLengths = getSequenceLengths(vehicleData);
      }
      const gap = 1; // Adjust gap duration as needed
      const maxGaps = getMaxGapsPerMinute(seqLengths, gap);
      
      // Update the pedestrian frequency input's max attribute
      const pedInput = document.getElementById('pedestrian-frequency');
      pedInput.max = Math.floor(maxGaps);
    }
    
    // Attach updatePedestrianMax to all vehicle input frequency
    document.addEventListener('DOMContentLoaded', function () {
      const vehicleInputs = [
        'nb_forward', 'nb_left', 'nb_right',
        'eb_forward', 'eb_left', 'eb_right',
        'sb_forward', 'sb_left', 'sb_right',
        'wb_forward', 'wb_left', 'wb_right'
      ];
    
      vehicleInputs.forEach(function(id) {
        const field = document.getElementById(id);
        if (field) {
          field.addEventListener('input', updatePedestrianMax);
        }
      });
    });

    // Additional listener for Traffic Light fields to update calculations
    document.addEventListener("DOMContentLoaded", function () {
      // These are your traffic light input IDs
      const trafficLightFields = ["tl_vmain", "tl_vright", "tl_hmain", "tl_hright"];
  
      trafficLightFields.forEach(id => {
        const field = document.getElementById(id);
        if (field) {
          // For each input change, call the function that updates your max calc
          field.addEventListener("input", () => {
            updatePedestrianMax(); 
            updateAndValidateTrafficSettings();
          });
        }
      });
    });

    document.addEventListener("DOMContentLoaded", function () {
      const inputIds = [
          "nb_forward", "nb_left", "nb_right",
          "eb_forward", "eb_left", "eb_right",
          "wb_forward", "wb_left", "wb_right",
          "sb_forward", "sb_left", "sb_right"
      ];

      inputIds.forEach(function (id) {
          const inputField = document.getElementById(id);
          if (inputField) {
              // Ensure valid integer values
              inputField.addEventListener("input", function () {
                  let value = this.value;

                  // Remove non-numeric characters
                  value = value.replace(/\D/g, '');

                  // Convert to integer
                  value = parseInt(value, 10);

                  // Ensure it’s within range
                  if (isNaN(value) || value < 0) {
                      value = 0;
                  } else if (value > 1000) {
                      value = 1000;
                  }

                  // Update field value
                  this.value = value;
              });

              // Ensure default value of 0 if left empty
              inputField.addEventListener("blur", function () {
                  if (this.value.trim() === "") {
                      this.value = 0;
                  }
              });
          }
      });
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

