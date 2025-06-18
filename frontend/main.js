/**
 * @fileoverview 
 * This file is responsible for animating the entire junction simulation. It manages:
 * - We render the junction, roads, traffic lights, pedestrians, and vehicles.
 * - By handling WebSocket communication with the backend, we have real-time updates.
 * - The canvas is dynamically resized based on user input (e.g., number of lanes), and window size.
 * - The animation loop is continuously ran in order to update the simulation, in real time.
 * - We manage pedestrian and vehicle movement, by retrieving the data from the backend and then animating here.
 * - Simulation speed is dynamically updated in real time, due to a listener for the speed slider.
 *
 * Features:
 * - We draw the road network and updates objects in real time.
 * - We handle signals for main traffic, pedestrian crossings, and right turns.
 * - The pedestrians are spawned after a traffic cycle (where right turn light, turn green -> red).
 * - We update car positions based on server-provided data, which is all calculated in backend.
 * - We sync traffic states, pedestrian lights, and vehicle positions with the backend.
 * - The simulation size dynamically adjust based on window size and based on the number of lanes.
 * - The slider allows real-time control over simulation speed, which instantly speeds everything up.
 *
 * Dependencies:
 * - junction.js: Used for rendering the road layout.
 * - config.js: Provides configuration settings for the canvas and junction.
 * - trafficLights.js: Handles traffic light rendering.
 * - pedestrianManager.js: Manages pedestrian movement.
 * - images.js: Loads car and pedestrian images.
 */

import { 
  junctionDrawing 
} from "./junction.js";

import { 
  getJunctionData, 
  junctionCanvas, 
  canvas2D 
} from "./config.js";

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

import { 
  spawnPedestrian, 
  updatePedestrians,
  drawPedestrians 
} from "./pedestrianManager.js";

import { 
  loadPedestrianPngs, 
  carPngs, 
  loadCarPngs 
} from "./images.js";

// We load the images here so they are available globally
loadPedestrianPngs();
loadCarPngs();

/**
 * This function updates the size of the canvas, based on the number of lanes.
 * This is called when the page loads, and when the user changes the number of lanes.
 * This dynamically sizes the canvas to fit the junction, and also the window size.
 */
function updateCanvasSize() {
  // Retrieve the number of lanes from the junction data, that user has inputted.
  const lanes = getJunctionData().numOfLanes;

  // Get the container and canvas elements, which we will use to dynamically size the canvas.
  const container = document.getElementById("junctionContainer");
  const canvas = document.getElementById("junctionCanvas");

  // We want the canvas to be square, so we set the width and height to the same value.
  canvas.width = canvas.height = container.clientHeight * (1 + lanes / 10);
}

/**
 * This is a global object that stores the state of the main traffic lights.
 * We will update this object when we receive messages from the server.
 */
let trafficLightStates = {
  north: { red: true, amber: false, green: false },
  east:  { red: true, amber: false, green: false },
  south: { red: true, amber: false, green: false },
  west:  { red: true, amber: false, green: false }
};

/**
 * These are global objects that store the state of the right-turn and pedestrian lights.
 * We will update these objects when we receive messages from the server.
 */
let rightTurnLightStates = {
  north: { off: true, on: false },
  east:  { off: true, on: false },
  south: { off: true, on: false },
  west:  { off: true, on: false }
};

/**
 * This is a global object that stores the state of the pedestrian lights.
 * We will update this object when we receive messages from the server.
 */
let pedestrianLightStates = {
  north: { off: true, on: false },
  east:  { off: true, on: false },
  south: { off: true, on: false },
  west:  { off: true, on: false }
};

/**
 * This is a global object that stores the state of the active pedestrian events.
 * However currently all are set to true or false at the same time, as we are not
 * implementing configurable pedestrian events based on direction in this scope.
 */
const activePedestrianEvents = {
  north: false,
  east: false,
  south: false,
  west: false
};

/**
 * This is a global array that stores the cars that are sent from the server.
 * We will update this array when we receive messages from the server.
 */
let carsFromServer = [];

/**
 * 
 */
function render() {
  // We first must clear the canvas before drawing anything new.
  canvas2D.clearRect(0, 0, junctionCanvas.width, junctionCanvas.height);

  // Firstly we draw the junction itself, and all of its roads etc..
  junctionDrawing();

  // Secondly we draw the main traffic lights controlling red, amber and green for forward/left turns.
  drawNorthTrafficLight(trafficLightStates.north);
  drawEastTrafficLight(trafficLightStates.east);
  drawSouthTrafficLight(trafficLightStates.south);
  drawWestTrafficLight(trafficLightStates.west);

  // Next we draw the pedestrian lights for each direction, which will all turn on and off at same time.
  drawNorthPuffinLight(pedestrianLightStates.north);
  drawEastPuffinLight(pedestrianLightStates.east);
  drawSouthPuffinLight(pedestrianLightStates.south);
  drawWestPuffinLight(pedestrianLightStates.west);

  // Next we draw the right turn lights for each direction, which controls right turns for the vehicles.
  drawNorthRightTurnLight(rightTurnLightStates.north);
  drawEastRightTurnLight(rightTurnLightStates.east);
  drawSouthRightTurnLight(rightTurnLightStates.south);
  drawWestRightTurnLight(rightTurnLightStates.west);

  // We then draw the pedestrians on the canvas, which all move at the same time for all directions.
  updatePedestrians();
  drawPedestrians();

  // As the cars are sent from the server, we draw them on the canvas.
  carsFromServer.forEach(car => {
    drawCarOnCanvas(car);
  });
}

/**
 * This function draws a car on the canvas, based on the car object that is passed in.
 * The car object contains all the relevant data for the car, such as its position, direction, and image.
 * Right turn movements are done in phases of the turn so must track angles.
 * 
 * @param {Object} car - The car object that we will draw on the canvas, storing relevant data. 
 */
function drawCarOnCanvas(car) {
  // Load the correct car image based on the car's pngIndex, which was randomly generated in backend.
  let png = carPngs[car.pngIndex];

  // Save the current canvas state
  canvas2D.save();

  // Translate to the car's position correct position
  canvas2D.translate(car.x, car.y);

  // We utilise a global angle variable to rotate the car image based on its direction.
  let angle = 0;

  // If the car is turning right we must rotate it by the correct angle, for current phase of movement, 
  if (car.turnType === "right") {
    angle = car.currentRightTurnAngle;
  } else { // else we rotate it based on the same angle for its direction.
    if (car.direction === "north") angle = 0;
    else if (car.direction === "east") angle = Math.PI / 2;
    else if (car.direction === "south") angle = Math.PI;
    else if (car.direction === "west") angle = -Math.PI / 2;
  }

  // Rotate the canvas by the angle, and draw the car image at the correct position.
  canvas2D.rotate(angle);

  // Draw the car image at the correct position, and size based on the car's width and height.
  canvas2D.drawImage(png, -car.width / 2, -car.height / 2, car.width, car.height);

  // Restore the canvas state
  canvas2D.restore();
}

/**
 * This function is called recursively to animate the junction.
 * It calls the render function, which draws the junction, traffic lights, pedestrians and cars.
 */
function animate() {
  requestAnimationFrame(animate);
  render();
}

/**
 * This is the WebSocket connection to the backend.
 * We connect to the backend on the same host, and listen for messages from the server.
 * We have callbacks for when the connection is opened, when a message is received, and when the connection is closed.
 */
const protocol = window.location.protocol === "https:" ? "wss" : "ws";
const ws = new WebSocket(`${protocol}://${window.location.host}/ws`);
// Make the WebSocket connection available globally.
window.ws = ws;  

// We listen for messages from the server, and update the client-side state based on the messages.
ws.onopen = () => {
  // We log to the console when we are connected to the backend for debugging. 
  console.log("Connected to backend");

  // We need to wait for the DOM to be ready before sending the canvas size to the server.
  setTimeout(() => {
    // We send the canvas size to the server, so it can size the canvas on its side.
    updateCanvasSize();

    // We send the canvas size to the server, so it can size the canvas on its side.
    const w = junctionCanvas.width;
    const h = junctionCanvas.height;

    // We log to the console when we send the canvas size to the server for debugging.
    console.log("Sending canvasSize:", w, h);

    // We send the canvas size to the server, so it can size the canvas on its side.
    ws.send(JSON.stringify({
      type: "canvasSize",
      width: w,
      height: h
    }));
  }, 500); // We wait 500ms before sending the canvas size to the server.
};

/**
 * We listen for messages from the server, and update the client-side state based on the messages.
 * We parse the message from the server, which is a JSON string.
 * We update the client-side state based on the messages from the server.
 *
 * @param {MessageEvent} evt - The WebSocket message event containing data from the server.
 */
ws.onmessage = (evt) => {
  // We parse the message from the server, which is a JSON string.
  const data = JSON.parse(evt.data);

  // We track the simulated time on the frontend, which is sent from the server, and then displayed.
  if (data.simulatedTime !== undefined) {
    document.getElementById("timeSimulated").textContent = `Time Simulated: ${data.simulatedTime}`;
  }

  // We update the client-side state based on the messages from the server.
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

  // We update the cars on the frontend based on the messages from the server.
  if (data.cars) {
    carsFromServer = data.cars;
  }
};

// We log to the console when we are disconnected from the backend for debugging.
ws.onclose = () => {
  console.log("Disconnected from backend");
};

/**
 * This is implemmented for a listener when the page loads in order to size our canvas
 * and then animate the rest of our junction and objects.
 */
window.addEventListener("load", () => {
  // We dynamically size the canvas based on the number of lanes, etc.
  updateCanvasSize();
  
  // We start the animation loop, which will call the render function to draw the junction, traffic lights, pedestrians and cars.
  animate();
});

/**
 * This is a slider on the junction Page which dynamically changes the simualtion speed.
 * We use this dynamically to speed up the junction and all of the objects including cars etc.
 */
slider.addEventListener("input", () => {
  // Retrieves the users required speed from the slider.
  const newSpeed = parseFloat(slider.value);

  // We update the UI to display this new speed.
  speedLabel.textContent = "Simulation Speed (" + newSpeed + ")";

  // Highlight the active tick mark on the slider
  tickMarks.forEach(tick => {
    tick.classList.toggle("activeTick", tick.textContent === slider.value);
  });

  // We send the update of the speed to the server:
  ws.send(JSON.stringify({
    type: "speedUpdate",
    speed: newSpeed
  }));
  
  // Update the client-side multiplier as well:
  window.simulationSpeedMultiplier = newSpeed;
});