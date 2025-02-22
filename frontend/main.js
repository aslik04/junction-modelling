/*************************************************************************
 * main.js
 *************************************************************************/

import { junctionDrawing } from "./junction.js";
import { getJunctionData, junctionCanvas, canvas2D } from "./config.js";
import {
  drawNorthTrafficLight,
  drawEastTrafficLight,
  drawSouthTrafficLight,
  drawWestTrafficLight,
  drawNorthPuffinLight,
  drawEastPuffinLight,
  drawSouthPuffinLight,
  drawWestPuffinLight,
  drawNorthRightTurnLight,
  drawEastRightTurnLight,
  drawSouthRightTurnLight,
  drawWestRightTurnLight
} from "./trafficLights.js";
import { spawnPedestrian, updatePedestrians, drawPedestrians } from "./pedestrianManager.js";
import { loadPedestrianPngs, carPngs, loadCarPngs } from "./images.js";

/*************************************************************************
 * Load images
 *************************************************************************/
loadPedestrianPngs();
loadCarPngs();

/*************************************************************************
 * Dynamically size the canvas
 *************************************************************************/
function updateCanvasSize() {
  const lanes = getJunctionData().numOfLanes;
  const container = document.getElementById("junctionContainer");
  const canvas = document.getElementById("junctionCanvas");
  // scale by lanes
  canvas.width = container.clientWidth * (1 + lanes / 10);
  canvas.height = container.clientHeight * (1 + lanes / 10);
}

/*************************************************************************
 * Local states for lights / pedestrians
 *************************************************************************/
let trafficLightStates = {
  north: { red: true, amber: false, green: false },
  east:  { red: true, amber: false, green: false },
  south: { red: true, amber: false, green: false },
  west:  { red: true, amber: false, green: false }
};
let rightTurnLightStates = {
  north: { off: true, on: false },
  east:  { off: true, on: false },
  south: { off: true, on: false },
  west:  { off: true, on: false }
};
let pedestrianLightStates = {
  north: { off: true, on: false },
  east:  { off: true, on: false },
  south: { off: true, on: false },
  west:  { off: true, on: false }
};

// Track active pedestrian events so we don't spawn duplicates
const activePedestrianEvents = {
  north: false,
  east: false,
  south: false,
  west: false
};

/*************************************************************************
 * Cars from server
 *************************************************************************/
let carsFromServer = [];

/*************************************************************************
 * The render function
 *************************************************************************/
function render() {
  canvas2D.clearRect(0, 0, junctionCanvas.width, junctionCanvas.height);

  // 1) Draw the junction
  junctionDrawing();

  // 2) Draw traffic lights
  drawNorthTrafficLight(trafficLightStates.north);
  drawEastTrafficLight(trafficLightStates.east);
  drawSouthTrafficLight(trafficLightStates.south);
  drawWestTrafficLight(trafficLightStates.west);

  // 3) Draw pedestrian lights
  drawNorthPuffinLight(pedestrianLightStates.north);
  drawEastPuffinLight(pedestrianLightStates.east);
  drawSouthPuffinLight(pedestrianLightStates.south);
  drawWestPuffinLight(pedestrianLightStates.west);

  // 4) Draw right-turn lights
  drawNorthRightTurnLight(rightTurnLightStates.north);
  drawEastRightTurnLight(rightTurnLightStates.east);
  drawSouthRightTurnLight(rightTurnLightStates.south);
  drawWestRightTurnLight(rightTurnLightStates.west);

  // 5) Update + draw pedestrians
  updatePedestrians();
  drawPedestrians();

  // 6) Draw cars from the server
  carsFromServer.forEach(car => {
    drawCarOnCanvas(car);
  });
}

/*************************************************************************
 * Draw a single car from the server
 *************************************************************************/
function drawCarOnCanvas(car) {
  let png = carPngs[car.pngIndex];

  canvas2D.save();
  canvas2D.translate(car.x, car.y);

  // If turnType is "right", rotate by car.currentRightTurnAngle
  let angle = 0;
  if (car.turnType === "right") {
    angle = car.currentRightTurnAngle;
  } else {
    if (car.direction === "north") angle = 0;
    else if (car.direction === "east") angle = Math.PI / 2;
    else if (car.direction === "south") angle = Math.PI;
    else if (car.direction === "west") angle = -Math.PI / 2;
  }
  canvas2D.rotate(angle);

  canvas2D.drawImage(png, -car.width / 2, -car.height / 2, car.width, car.height);

  canvas2D.restore();
}

/*************************************************************************
 * The animation loop
 *************************************************************************/
function animate() {
  requestAnimationFrame(animate);
  render();
}

/*************************************************************************
 * Connect to the backend via WebSocket
 *************************************************************************/
const ws = new WebSocket("ws://localhost:8000/ws");
window.ws = ws;  // Make ws available globally

// Only send data after the socket is open
ws.onopen = () => {
  console.log("Connected to backend");
  
  // Now it's safe to call ws.send(...)
  const w = junctionCanvas.width;
  const h = junctionCanvas.height;
  ws.send(JSON.stringify({
    type: "canvasSize",
    width: w,
    height: h
  }));
};

ws.onmessage = (evt) => {
  const data = JSON.parse(evt.data);

  // traffic light states
  if (data.trafficLightStates) {
    trafficLightStates = data.trafficLightStates;
  }
  if (data.rightTurnLightStates) {
    rightTurnLightStates = data.rightTurnLightStates;
  }
  if (data.pedestrianLightStates) {
    pedestrianLightStates = data.pedestrianLightStates;
    // spawn pedestrians if needed
    ["north", "east", "south", "west"].forEach(direction => {
      if (pedestrianLightStates[direction].on && !activePedestrianEvents[direction]) {
        spawnPedestrian(direction);
        activePedestrianEvents[direction] = true;
      }
      if (!pedestrianLightStates[direction].on) {
        activePedestrianEvents[direction] = false;
      }
    });
  }

  // If server sends "cars"
  if (data.cars) {
    carsFromServer = data.cars;
  }
};

ws.onclose = () => {
  console.log("Disconnected from backend");
};

/*************************************************************************
 * On page load
 *************************************************************************/
window.addEventListener("load", () => {
  // 1) Size the canvas
  updateCanvasSize();
  // 2) DO NOT call ws.send(...) here again or you'll get "Still in CONNECTING"
  // Instead, rely on the ws.onopen callback

  // 3) Start animation
  animate();
});

slider.addEventListener("input", () => {
  const newSpeed = parseFloat(slider.value);
  speedLabel.textContent = "Vehicle Speed (" + newSpeed + ")";
  tickMarks.forEach(tick => {
    tick.classList.toggle("activeTick", tick.textContent === slider.value);
  });
  // Send speed update to the server:
  ws.send(JSON.stringify({
    type: "speedUpdate",
    speed: newSpeed
  }));
  // Update the client-side multiplier as well:
  window.simulationSpeedMultiplier = newSpeed;
});
