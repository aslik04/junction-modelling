/**
 * @fileoverview This file handles the rendering of different types of traffic lights 
 * (main lights, puffin lights, and right-turn lights) on a four-way junction using an HTML canvas.
 * We provide functions to position, draw, and update traffic signals according to their sequences.
 * The traffic lights are drawn using a combination of shapes and text, with the canvas API.
 * Main lights consist of red, amber, and green signals, puffin lights are white or grey, 
 * and right-turn lights are green or red.
 * Where the puffin lights are on the top left of the main light 
 * and the right-turn lights are on the bottom right.
 *
 * Features:
 * - We draw main traffic lights with red, amber, and green signals, controlling left and forward turns.
 * - We draw pedestrian-specific traffic lights, which stops all other lights.
 * - We render dedicated right-turn signals with arrow indicators, for right turns only.
 * - We use junction data to place lights in the correct locations.
 * - We utilise translations and rotations for accurate placement.
 *
 * Dependencies:
 * - config.js: Provides lane dimensions and junction data for accurate positioning.
 */

import { 
    canvas2D, 
    getJunctionData, 
    puffinCrossingStripeLength, 
    pixelWidthOfLane 
} from "./config.js";

/**
 * This function draws the background of a traffic light, essentially the housing for the lights.
 *
 * @param {number} lightWidth - Width of the traffic light.
 * @param {number} height - Height of the traffic light.
 */
function drawTrafficLightBackground(lightWidth, height) {
    // Begins the drawing of the traffic light background.
    canvas2D.beginPath();

    // Draws a rounded rectangle for the traffic light background.
    canvas2D.moveTo(5, 0);
    canvas2D.lineTo(lightWidth - 5, 0);
    canvas2D.quadraticCurveTo(lightWidth, 0, lightWidth, 5);
    canvas2D.lineTo(lightWidth, height - 5);
    canvas2D.quadraticCurveTo(lightWidth, height, lightWidth - 5, height);
    canvas2D.lineTo(5, height);
    canvas2D.quadraticCurveTo(0, height, 0, height - 5);
    canvas2D.lineTo(0, 5);
    canvas2D.quadraticCurveTo(0, 0, 5, 0);

    // Closes the path for the background.
    canvas2D.closePath();
    
    // Fills the background with a dark grey colour, and develops an outline.
    canvas2D.fillStyle = "#222";
    canvas2D.fill();
    canvas2D.strokeStyle = "#555";
    canvas2D.lineWidth = 2;
    canvas2D.stroke();
} 


/**
 * This function draws the main traffic light, which consists of three lights: red, amber, and green.
 * Which can be turned on or off depending on the sequence object passed in.
 * Also is modifiable to draw for each and every direction of the junction, based on angles and coords.
 *
 * @param {number} xCoord - X-coordinate of the light's position.
 * @param {number} yCoord - Y-coordinate of the light's position.
 * @param {number} angle - Rotation angle of the light.
 * @param {Object} sequence - Object specifying which lights are active.
 */
function drawTrafficLight(xCoord, yCoord, angle, sequence = { red: false, amber: false, green: false }) {
    // Data concerning the size of the main traffic light and the radius of the light.
    const width = pixelWidthOfLane;
    const height = pixelWidthOfLane * 3;
    const radiusOfLight = width / 3;
    
    // Object containing the colours of the lights, depedning on boolean conditions.
    // If the light is on, the colour is bright, otherwise it is a darker shade of the colour.
    const colours = {
        red:   sequence.red   ? "#FF0000" : "#330000",
        amber: sequence.amber ? "#FFBF00" : "#332200",
        green: sequence.green ? "#00FF00" : "#003300"
    }

    // Array containing the locations of the lights.
    const locations = [
        { colour: 'red',   startPos: height * 1/6 },  
        { colour: 'amber', startPos: height * 1/2 },
        { colour: 'green', startPos: height * 5/6 }   
    ]

    // Saves the current state of the canvas.
    canvas2D.save();

    // Translates the canvas to the specified coordinates and rotates it by the specified angle.
    canvas2D.translate(xCoord, yCoord);
    canvas2D.rotate(angle);

    // Ensures the backgorund of the light is drawn first.
    drawTrafficLightBackground(width, height);

    // Draws each light in the traffic light.
    locations.forEach(({ colour, startPos }) => {
        canvas2D.beginPath();
        canvas2D.arc(width / 2, startPos, radiusOfLight, 0, 2 * Math.PI);
        canvas2D.fillStyle = colours[colour];
        canvas2D.fill();
    });

    // Restores the canvas to its previous state.
    canvas2D.restore();
}

/**
 * This function draws the main puffin light, which consists of a single light.
 * This light is placed on the top left of the main light besides the red light.
 * It is either off and grey or white and on, controls the pedestrian crossing.
 * 
 * @param {number} xCoord - X-coordinate of the light's position.
 * @param {number} yCoord - Y-coordinate of the light's position.
 * @param {number} angle - Rotation angle of the light.
 * @param {Object} sequence - Object specifying whether the light is on or off.
 */
function drawPuffinLight(xCoord, yCoord, angle, sequence = { off: true, on: false }) {
    // Data concerning the size of the puffin light and the radius of the light.
    const size = pixelWidthOfLane;
    const radiusOfLight = size / 3;
  
    // Colour of the light, either white or grey, when boolean object is on or off respectively.
    const colour = sequence.on ? "#FFFFFF" : "grey";
  
    // Saves the current state of the canvas.
    canvas2D.save();

    // Translates the canvas to the specified coordinates and rotates it by the specified angle.
    canvas2D.translate(xCoord, yCoord);
    canvas2D.rotate(angle);
  
    // Ensures the backgorund of the puffin light is drawn first.
    drawTrafficLightBackground(size, size);
  
    // Draws the puffin light.
    const centre = size / 2;
    canvas2D.beginPath();
    canvas2D.arc(centre, centre, radiusOfLight, 0, 2 * Math.PI);
    canvas2D.fillStyle = colour;
    canvas2D.fill();
  
    // Draws the letter 'P' in the centre of the light, to signal to viewer it is for pedestrian.
    canvas2D.font = "bold 10px Poppins";
    canvas2D.textAlign = "center";
    canvas2D.textBaseline = "middle";
    canvas2D.fillStyle = "#FFFFFF";
    canvas2D.fillText("P", centre, centre + 1);
  
    // Restores the canvas to its previous state.
    canvas2D.restore();
}

/**
 * This function draws the main right turn light, which consists of a single light.
 * This light is placed on the bottom right of the main light besides the green light.
 * It is either off and red or green and on, controls the right turn of the vehicles.
 *
 * @param {number} xCoord - X-coordinate of the light's position.
 * @param {number} yCoord - Y-coordinate of the light's position.
 * @param {number} angle - Rotation angle of the light.
 * @param {Object} sequence - Object specifying whether the light is on or off.
 */
function drawRightTurnLight(xCoord, yCoord, angle, sequence = { off: true, on: false }) {
    // Data concerning the size of the right turn light and the radius of the light.
    const size = pixelWidthOfLane;
    const radiusOfLight = size / 3;
  
    // Colour of the light, either green or red, when boolean object is on or off respectively.
    const colour = sequence.on ? "#00FF00" : "red";
  
    // Saves the current state of the canvas.
    canvas2D.save();

    // Translates the canvas to the specified coordinates and rotates it by the specified angle.
    canvas2D.translate(xCoord, yCoord);
    canvas2D.rotate(angle);
  
    // Ensures the backgorund of the right turn light is drawn first.
    drawTrafficLightBackground(size, size);
  
    // Draws the right turn light.
    const centre = size / 2;
    canvas2D.beginPath();
    canvas2D.arc(centre, centre, radiusOfLight, 0, 2 * Math.PI);
    canvas2D.fillStyle = colour;
    canvas2D.fill();
  
    // Draws the arrow '→' in the centre of the light, to signal to viewer it is for right turn.
    canvas2D.font = "bold 10px Poppins";
    canvas2D.textAlign = "center";
    canvas2D.textBaseline = "middle";
    canvas2D.fillStyle = "#FFFFFF";
    canvas2D.fillText("→", centre, centre);  
    
    // Restores the canvas to its previous state.
    canvas2D.restore();
}

/**
 * This function draws the main traffic lights for the North direction of the junction.
 * 
 * @param {Object} sequence - Object specifying which lights are active.
 */
export function drawNorthTrafficLight(sequence) {
    const { 
        bottomHorizontal, 
        leftVertical
    } = getJunctionData();
    
    // This is dimensions for the lights arbitrarily calculated to scale according to junction environment.
    const widthOfPC = puffinCrossingStripeLength() + 5
    const xCoord = leftVertical - pixelWidthOfLane * 2;
    const yCoord = bottomHorizontal + widthOfPC;

    // Draws the traffic light for the North direction.
    drawTrafficLight(xCoord, yCoord, 0, sequence);
}

/**
 * This function draws the main traffic lights for the East direction of the junction.
 * 
 * @param {Object} sequence - Object specifying which lights are active
 */
export function drawEastTrafficLight(sequence) {
    const { 
        leftVertical
    } = getJunctionData();

    // This is dimensions for the lights arbitrarily calculated to scale according to junction environment.
    const widthOfPC = puffinCrossingStripeLength() + 5;
    const xCoord = leftVertical - widthOfPC;
    const yCoord = leftVertical - pixelWidthOfLane * 2;

    // Draws the traffic light for the East direction.
    drawTrafficLight(xCoord, yCoord, Math.PI / 2, sequence);
}

/**
 * This function draws the main traffic lights for the South direction of the junction.
 * 
 * @param {Object} sequence - Object specifying which lights are active.
 */
export function drawSouthTrafficLight(sequence) {
    const { 
        rightVertical, 
        topHorizontal 
    } = getJunctionData();

    // This is dimensions for the lights arbitrarily calculated to scale according to junction environment.
    const widthOfPC = puffinCrossingStripeLength() + 5;
    const xCoord = rightVertical + pixelWidthOfLane * 2;
    const yCoord = topHorizontal - widthOfPC;

    // Draws the traffic light for the South direction.
    drawTrafficLight(xCoord, yCoord, Math.PI, sequence);
}

/**
 * This function draws the main traffic lights for the West direction of the junction.
 * 
 * @param {Object} sequence - Object specifying which lights are active.
 */
export function drawWestTrafficLight(sequence) {
    const { 
        rightVertical 
    } = getJunctionData();

    // This is dimensions for the lights arbitrarily calculated to scale according to junction environment.
    const widthOfPC = puffinCrossingStripeLength() + 5;
    const xCoord = rightVertical + widthOfPC;
    const yCoord = rightVertical + pixelWidthOfLane * 2;

    // Draws the traffic light for the West direction.
    drawTrafficLight(xCoord, yCoord, -Math.PI / 2, sequence);
}

/**
 * This function draws the puffin light for the North direction of the junction.
 * 
 * @param {Object} sequence - Object specifying whether the light is on or off.
 */
export function drawNorthPuffinLight(sequence) {
    const { 
        bottomHorizontal, 
        leftVertical
    } = getJunctionData();
    
    // This is dimensions for the puffin lights arbitrarily calculated to scale according to junction environment.
    const widthOfPC = puffinCrossingStripeLength() + 5;
    const xCoord = leftVertical - pixelWidthOfLane * 3;
    const yCoord = bottomHorizontal + widthOfPC;

    // Draws the puffin light for the North direction.
    drawPuffinLight(xCoord, yCoord, 0, sequence);
}

/**
 * This function draws the puffin light for the East direction of the junction.
 * 
 * @param {Object} sequence - Object specifying whether the light is on or off.
 */
export function drawEastPuffinLight(sequence) {
    const { 
        leftVertical
    } = getJunctionData();

    // This is dimensions for the puffin lights arbitrarily calculated to scale according to junction environment.
    const widthOfPC = puffinCrossingStripeLength() + 5;
    const xCoord = leftVertical - widthOfPC;
    const yCoord = leftVertical - pixelWidthOfLane * 3;

    // Draws the puffin light for the East direction.
    drawPuffinLight(xCoord, yCoord, Math.PI / 2, sequence);
}

/**
 * This function draws the puffin light for the South direction of the junction.
 * 
 * @param {Object} sequence - Object specifying whether the light is on or off.
 */
export function drawSouthPuffinLight(sequence) {
    const { 
        rightVertical, 
        topHorizontal 
    } = getJunctionData();

    // This is dimensions for the puffin lights arbitrarily calculated to scale according to junction environment.
    const widthOfPC = puffinCrossingStripeLength() + 5;
    const xCoord = rightVertical + pixelWidthOfLane * 3;
    const yCoord = topHorizontal - widthOfPC;

    // Draws the puffin light for the South direction.
    drawPuffinLight(xCoord, yCoord, Math.PI, sequence);
}

/**
 * This function draws the puffin light for the West direction of the junction.
 * 
 * @param {Object} sequence - Object specifying whether the light is on or off.
 */
export function drawWestPuffinLight(sequence) {
    const { 
        rightVertical 
    } = getJunctionData();

    // This is dimensions for the puffin lights arbitrarily calculated to scale according to junction environment.
    const widthOfPC = puffinCrossingStripeLength() + 5;
    const xCoord = rightVertical + widthOfPC;
    const yCoord = rightVertical + pixelWidthOfLane * 3;

    // Draws the puffin light for the West direction.
    drawPuffinLight(xCoord, yCoord, -Math.PI / 2, sequence);
}

/**
 * This function draws the right turn light for the North direction of the junction.
 */
export function drawNorthRightTurnLight(sequence) {
    const { 
        bottomHorizontal, 
        leftVertical
    } = getJunctionData();
    
    // This is dimensions for the right turn lights arbitrarily calculated to scale according to junction environment.
    const widthOfPC = puffinCrossingStripeLength() + 5;
    const xCoord = leftVertical - pixelWidthOfLane;
    const yCoord = bottomHorizontal + widthOfPC + pixelWidthOfLane * 2;

    // Draws the right turn light for the North direction.
    drawRightTurnLight(xCoord, yCoord, 0, sequence);
}

/**
 * This function draws the right turn light for the East direction of the junction.
 * 
 * @param {Object} sequence - Object specifying whether the light is on or off.
 */
export function drawEastRightTurnLight(sequence) {
    const { 
        leftVertical
    } = getJunctionData();

    // This is dimensions for the right turn lights arbitrarily calculated to scale according to junction environment.
    const widthOfPC = puffinCrossingStripeLength() + 5;
    const xCoord = leftVertical - widthOfPC - pixelWidthOfLane * 2;
    const yCoord = leftVertical - pixelWidthOfLane;

    // Draws the right turn light for the East direction.
    drawRightTurnLight(xCoord, yCoord, Math.PI / 2, sequence);
}

/**
 * This function draws the right turn light for the South direction of the junction.
 */
export function drawSouthRightTurnLight(sequence) {
    const { 
        rightVertical, 
        topHorizontal 
    } = getJunctionData();

    // This is dimensions for the right turn lights arbitrarily calculated to scale according to junction environment.
    const widthOfPC = puffinCrossingStripeLength() + 5;
    const xCoord = rightVertical + pixelWidthOfLane;
    const yCoord = topHorizontal - widthOfPC - pixelWidthOfLane * 2;

    // Draws the right turn light for the South direction.
    drawRightTurnLight(xCoord, yCoord, Math.PI, sequence);
}

/**
 * This function draws the right turn light for the West direction of the junction.
 */
export function drawWestRightTurnLight(sequence) {
    const { 
        rightVertical 
    } = getJunctionData();

    // This is dimensions for the right turn lights arbitrarily calculated to scale according to junction environment.
    const widthOfPC = puffinCrossingStripeLength() + 5;
    const xCoord = rightVertical + widthOfPC + pixelWidthOfLane * 2;
    const yCoord = rightVertical + pixelWidthOfLane;

    // Draws the right turn light for the West direction.
    drawRightTurnLight(xCoord, yCoord, -Math.PI / 2, sequence);
}