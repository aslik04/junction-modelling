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
import { loadPedestrianPngs } from "./images.js";

loadPedestrianPngs();

function updateCanvasSize() {
  const lanes = getJunctionData().numOfLanes;
  const container = document.getElementById("junctionContainer");
  const canvas = document.getElementById("junctionCanvas");
  canvas.width = container.clientWidth * (1 + lanes / 10);
  canvas.height = container.clientHeight * (1 + lanes / 10);
}

// Local state copies for the simulation
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

// To prevent spawning duplicate pedestrians for the same event,
// track active pedestrian events for each direction.
const activePedestrianEvents = {
  north: false,
  east: false,
  south: false,
  west: false
};

function render() {
  // Clear the entire canvas
  canvas2D.clearRect(0, 0, junctionCanvas.width, junctionCanvas.height);

  // Draw the junction (roads, lanes, crosswalks, etc.)
  junctionDrawing();

  // Draw traffic lights
  drawNorthTrafficLight(trafficLightStates.north);
  drawEastTrafficLight(trafficLightStates.east);
  drawSouthTrafficLight(trafficLightStates.south);
  drawWestTrafficLight(trafficLightStates.west);

  // Draw pedestrian (puffin) lights
  drawNorthPuffinLight(pedestrianLightStates.north);
  drawEastPuffinLight(pedestrianLightStates.east);
  drawSouthPuffinLight(pedestrianLightStates.south);
  drawWestPuffinLight(pedestrianLightStates.west);

  // Draw right-turn lights
  drawNorthRightTurnLight(rightTurnLightStates.north);
  drawEastRightTurnLight(rightTurnLightStates.east);
  drawSouthRightTurnLight(rightTurnLightStates.south);
  drawWestRightTurnLight(rightTurnLightStates.west);

  // Update and draw any active pedestrians
  updatePedestrians();
  drawPedestrians();
}

function animate() {
  requestAnimationFrame(animate);
  render();
}

const ws = new WebSocket("ws://localhost:8000/ws");

ws.onopen = () => {
  console.log("Connected to backend");
};

ws.onmessage = (evt) => {
  const data = JSON.parse(evt.data);
  if (data.trafficLightStates) {
    trafficLightStates = data.trafficLightStates;
  }
  if (data.rightTurnLightStates) {
    rightTurnLightStates = data.rightTurnLightStates;
  }
  if (data.pedestrianLightStates) {
    pedestrianLightStates = data.pedestrianLightStates;

    // For each direction, if the pedestrian light is on and no pedestrian is active for that event, spawn one.
    ["north", "east", "south", "west"].forEach(direction => {
      if (pedestrianLightStates[direction].on && !activePedestrianEvents[direction]) {
        spawnPedestrian(direction);
        activePedestrianEvents[direction] = true;
      }
      // Reset the flag when the light is off, so new events can spawn pedestrians.
      if (!pedestrianLightStates[direction].on) {
        activePedestrianEvents[direction] = false;
      }
    });
  }
};

ws.onclose = () => {
  console.log("Disconnected from backend");
};

window.addEventListener("load", () => {
  updateCanvasSize();
  animate();
});
