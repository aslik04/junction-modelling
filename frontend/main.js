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

function updateCanvasSize() {
  const lanes = getJunctionData().numOfLanes;
  const middleSection = document.getElementById("junctionContainer");
  const canvas = document.getElementById("junctionCanvas");
  canvas.width = middleSection.clientWidth * (1 + (lanes / 10));
  canvas.height = middleSection.clientHeight * (1 + (lanes / 10));
}

let trafficLightStates = {
  north: { red: true, amber: false, green: false },
  east:  { red: true, amber: false, green: false },
  south: { red: true, amber: false, green: false },
  west:  { red: true, amber: false, green: false },
};
let rightTurnLightStates = {
  north: { off: true, on: false },
  east:  { off: true, on: false },
  south: { off: true, on: false },
  west:  { off: true, on: false },
};
let pedestrianLightStates = {
  north: { off: true, on: false },
  east:  { off: true, on: false },
  south: { off: true, on: false },
  west:  { off: true, on: false },
};

function render() {
  canvas2D.clearRect(0, 0, junctionCanvas.width, junctionCanvas.height);
  junctionDrawing();
  
  drawNorthTrafficLight(trafficLightStates.north);
  drawEastTrafficLight(trafficLightStates.east);
  drawSouthTrafficLight(trafficLightStates.south);
  drawWestTrafficLight(trafficLightStates.west);
  
  drawNorthPuffinLight(pedestrianLightStates.north);
  drawEastPuffinLight(pedestrianLightStates.east);
  drawSouthPuffinLight(pedestrianLightStates.south);
  drawWestPuffinLight(pedestrianLightStates.west);
  
  drawNorthRightTurnLight(rightTurnLightStates.north);
  drawEastRightTurnLight(rightTurnLightStates.east);
  drawSouthRightTurnLight(rightTurnLightStates.south);
  drawWestRightTurnLight(rightTurnLightStates.west);
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
  }
};

ws.onclose = () => {
  console.log("Disconnected from backend");
};

window.addEventListener("load", () => {
  updateCanvasSize();
  junctionDrawing();
  animate();
});
