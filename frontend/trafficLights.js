/**
 * @fileoverview
 */

import { 
    canvas2D, 
    getJunctionData, 
    puffinCrossingStripeLength, 
    pixelWidthOfLane 
} from "./config.js";

/**
 * 
 */
function drawTrafficLightBackground(lightWidth, height) {
    canvas2D.beginPath();

    canvas2D.moveTo(5, 0);
    canvas2D.lineTo(lightWidth - 5, 0);
    canvas2D.quadraticCurveTo(lightWidth, 0, lightWidth, 5);

    canvas2D.lineTo(lightWidth, height - 5);
    canvas2D.quadraticCurveTo(lightWidth, height, lightWidth - 5, height);
    canvas2D.lineTo(5, height);

    canvas2D.quadraticCurveTo(0, height, 0, height - 5);
    canvas2D.lineTo(0, 5);
    canvas2D.quadraticCurveTo(0, 0, 5, 0);

    canvas2D.closePath();
    
    canvas2D.fillStyle = "#222";
    canvas2D.fill();
    canvas2D.strokeStyle = "#555";
    canvas2D.lineWidth = 2;
    canvas2D.stroke();
} 

/**
 * 
 */
function drawTrafficLight(xCoord, yCoord, angle, sequence = { red: false, amber: false, green: false }) {
    const width = pixelWidthOfLane;
    const height = pixelWidthOfLane * 3;
    const radiusOfLight = width / 3;
    
    const colours = {
        red:   sequence.red   ? "#FF0000" : "#330000",
        amber: sequence.amber ? "#FFBF00" : "#332200",
        green: sequence.green ? "#00FF00" : "#003300"
    }

    const locations = [
        { colour: 'red',   startPos: height * 1/6 },  
        { colour: 'amber', startPos: height * 1/2 },
        { colour: 'green', startPos: height * 5/6 }   
    ]

    canvas2D.save();
    canvas2D.translate(xCoord, yCoord);
    canvas2D.rotate(angle);

    drawTrafficLightBackground(width, height);

    locations.forEach(({ colour, startPos }) => {
        canvas2D.beginPath();
        canvas2D.arc(width / 2, startPos, radiusOfLight, 0, 2 * Math.PI);
        canvas2D.fillStyle = colours[colour];
        canvas2D.fill();
    });

    canvas2D.restore();
}

/**
 * 
 */
function drawPuffinLight(xCoord, yCoord, angle, sequence = { off: true, on: false }) {
    const size = pixelWidthOfLane;
    const radiusOfLight = size / 3;
  
    const colour = sequence.on ? "#FFFFFF" : "grey";
  
    canvas2D.save();
    canvas2D.translate(xCoord, yCoord);
    canvas2D.rotate(angle);
  
    drawTrafficLightBackground(size, size);
  
    const centre = size / 2;
  
    canvas2D.beginPath();
    canvas2D.arc(centre, centre, radiusOfLight, 0, 2 * Math.PI);
    canvas2D.fillStyle = colour;
    canvas2D.fill();
  
    canvas2D.font = "bold 10px Poppins";
    canvas2D.textAlign = "center";
    canvas2D.textBaseline = "middle";
    canvas2D.fillStyle = "#FFFFFF";
    canvas2D.fillText("P", centre, centre + 1);
  
    canvas2D.restore();
}

/**
 * 
 */
function drawRightTurnLight(xCoord, yCoord, angle, sequence = { off: true, on: false }) {
    const size = pixelWidthOfLane;
    const radiusOfLight = size / 3;
  
    const colour = sequence.on ? "#00FF00" : "grey";
  
    canvas2D.save();
    canvas2D.translate(xCoord, yCoord);
    canvas2D.rotate(angle);
  
    drawTrafficLightBackground(size, size);
  
    const centre = size / 2;
  
    canvas2D.beginPath();
    canvas2D.arc(centre, centre, radiusOfLight, 0, 2 * Math.PI);
    canvas2D.fillStyle = colour;
    canvas2D.fill();
  
    canvas2D.font = "bold 10px Poppins";
    canvas2D.textAlign = "center";
    canvas2D.textBaseline = "middle";
    canvas2D.fillStyle = "#FFFFFF";
    canvas2D.fillText("→", centre, centre);  
    
    canvas2D.restore();
}

/**
 * 
 */
export function drawNorthTrafficLight(sequence) {
    const { 
        bottomHorizontal, 
        leftVertical
    } = getJunctionData();
    
    const widthOfPC = puffinCrossingStripeLength() + 5;

    const xCoord = leftVertical - pixelWidthOfLane - 20;
    const yCoord = bottomHorizontal + widthOfPC;

    drawTrafficLight(xCoord, yCoord, 0, sequence);
}

/**
 * 
 */
export function drawEastTrafficLight(sequence) {
    const { 
        leftVertical
    } = getJunctionData();

    const widthOfPC = puffinCrossingStripeLength() + 5;

    const xCoord = leftVertical - widthOfPC;
    const yCoord = leftVertical - pixelWidthOfLane - 20;

    drawTrafficLight(xCoord, yCoord, Math.PI / 2, sequence);
}

/**
 * 
 */
export function drawSouthTrafficLight(sequence) {
    const { 
        rightVertical, 
        topHorizontal 
    } = getJunctionData();

    const widthOfPC = puffinCrossingStripeLength() + 5;

    const xCoord = rightVertical + pixelWidthOfLane + 20;
    const yCoord = topHorizontal - widthOfPC;

    drawTrafficLight(xCoord, yCoord, Math.PI, sequence);
}

/**
 * 
 */
export function drawWestTrafficLight(sequence) {
    const { 
        rightVertical 
    } = getJunctionData();

    const widthOfPC = puffinCrossingStripeLength() + 5;

    const xCoord = rightVertical + widthOfPC;
    const yCoord = rightVertical + pixelWidthOfLane + 20;

    drawTrafficLight(xCoord, yCoord, -Math.PI / 2, sequence);
}

/**
 * 
 */
export function drawNorthPuffinLight(sequence) {
    const { 
        bottomHorizontal, 
        leftVertical
    } = getJunctionData();
    
    const widthOfPC = puffinCrossingStripeLength() + 5;

    const xCoord = leftVertical - pixelWidthOfLane - 40;
    const yCoord = bottomHorizontal + widthOfPC;

    drawPuffinLight(xCoord, yCoord, 0, sequence);
}

/**
 * 
 */
export function drawEastPuffinLight(sequence) {
    const { 
        leftVertical
    } = getJunctionData();

    const widthOfPC = puffinCrossingStripeLength() + 5;

    const xCoord = leftVertical - widthOfPC;
    const yCoord = leftVertical - pixelWidthOfLane - 40;

    drawPuffinLight(xCoord, yCoord, Math.PI / 2, sequence);
}

/**
 * 
 */
export function drawSouthPuffinLight(sequence) {
    const { 
        rightVertical, 
        topHorizontal 
    } = getJunctionData();

    const widthOfPC = puffinCrossingStripeLength() + 5;

    const xCoord = rightVertical + pixelWidthOfLane + 40;
    const yCoord = topHorizontal - widthOfPC;

    drawPuffinLight(xCoord, yCoord, Math.PI, sequence);
}

/**
 * 
 */
export function drawWestPuffinLight(sequence) {
    const { 
        rightVertical 
    } = getJunctionData();

    const widthOfPC = puffinCrossingStripeLength() + 5;

    const xCoord = rightVertical + widthOfPC;
    const yCoord = rightVertical + pixelWidthOfLane + 40;

    drawPuffinLight(xCoord, yCoord, -Math.PI / 2, sequence);
}

/**
 * 
 */
export function drawNorthRightTurnLight(sequence) {
    const { 
        bottomHorizontal, 
        leftVertical
    } = getJunctionData();
    
    const widthOfPC = puffinCrossingStripeLength() + 5;

    const xCoord = leftVertical - pixelWidthOfLane;
    const yCoord = bottomHorizontal + widthOfPC + 40;

    drawRightTurnLight(xCoord, yCoord, 0, sequence);
}

/**
 * 
 */
export function drawEastRightTurnLight(sequence) {
    const { 
        leftVertical
    } = getJunctionData();

    const widthOfPC = puffinCrossingStripeLength() + 5;

    const xCoord = leftVertical - widthOfPC - 40;
    const yCoord = leftVertical - pixelWidthOfLane;

    drawRightTurnLight(xCoord, yCoord, Math.PI / 2, sequence);
}

/**
 * 
 */
export function drawSouthRightTurnLight(sequence) {
    const { 
        rightVertical, 
        topHorizontal 
    } = getJunctionData();

    const widthOfPC = puffinCrossingStripeLength() + 5;

    const xCoord = rightVertical + pixelWidthOfLane;
    const yCoord = topHorizontal - widthOfPC - 40;

    drawRightTurnLight(xCoord, yCoord, Math.PI, sequence);
}

/**
 * 
 */
export function drawWestRightTurnLight(sequence) {
    const { 
        rightVertical 
    } = getJunctionData();

    const widthOfPC = puffinCrossingStripeLength() + 5;

    const xCoord = rightVertical + widthOfPC + 40;
    const yCoord = rightVertical + pixelWidthOfLane;

    drawRightTurnLight(xCoord, yCoord, -Math.PI / 2, sequence);
}