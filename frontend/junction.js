/**
 * @fileoverview
 */

import { 
    junctionCanvas, 
    canvas2D, 
    inputNumOfLanes, 
    pixelWidthOfLane, 
    pixelThicknessOfPC, 
    pixelGapOfPCStripes, 
    colourOfRoad, 
    colourOfLaneMarking, 
    colourOfBackground, 
    puffinCrossingStripeLength, 
    getJunctionData
} from "./config.js";

/**
 * Main method which renders the entire junction, by utilising helper methods detailed by file. 
 * Draws all roads, lanes, puffin crossings of the entire 4 way junction using predefined colours. 
 * Canvas is cleared and each element of the junction is drawn based on user input.
 */
export function junctionDrawing() {
    // To prevent repeated code utilised method with returns object of data regarding junction
    const {roadSize, canvasX, canvasY, topHorizontal, bottomHorizontal, leftVertical, rightVertical} = getJunctionData();
    
    // Clears and fills the canvas with a green colour for background.
    canvas2D.fillStyle = colourOfBackground;
    canvas2D.fillRect(0, 0, junctionCanvas.width, junctionCanvas.height);

    // Drawing of the roads on canvas.
    canvas2D.fillStyle = colourOfRoad;
    // Horizontal Roads (East and West).
    canvas2D.fillRect(0, topHorizontal, junctionCanvas.width, roadSize);
    // Vertical Roads (North and South).
    canvas2D.fillRect(leftVertical, 0, roadSize, junctionCanvas.height);

    // Drawing for the markings in lanes and the puffin crossing for each direction.
    drawLanes(numOfLanes, topHorizontal, bottomHorizontal, leftVertical, rightVertical, canvasX, canvasY);
    drawPuffinCrossing(topHorizontal, bottomHorizontal, leftVertical, rightVertical);
}

/**
 * Draws dashed lane markings in each of the 4 quadrants of the cardinal directions (NESW). 
 * Solid white line in centre of each road, to divide incoming and outgoing traffic.
 * 
 * @param {number} numOfLanes : Number of lanes user inputted.
 * @param {number} topHorizontal : Y-coordinate of top of the edge of horizontal road.
 * @param {number} bottomHorizontal : Y-coordinate of bottom of the edge of the horizontal road.
 * @param {number} leftVertical : X-coordinate of left edge of the vertical road.
 * @param {number} rightVertical : X-coordinate of right edge of the vertical road.
 * @param {number} canvasX : X-coordinate of the centre of the junction.
 * @param {number} canvasY : Y-coordinate of the centre of the junction.
 */
export function drawLanes(numOfLanes, topHorizontal, bottomHorizontal, leftVertical, rightVertical, canvasX, canvasY) {
    // Finds width of puffin crossing, so the road markings do not cross over into puffin crossing.
    const widthOfPC = puffinCrossingStripeLength();

    // Colour and width of the dashed lane markings.
    canvas2D.strokeStyle = colourOfLaneMarking;
    canvas2D.lineWidth = 2;

    // The pattern of the dashed lane markings (15 pixels solid, 10 pixels gap).
    canvas2D.setLineDash([15, 10]);

    // Above (centre LINE) drawing dashed horizontal lane markings in white (EAST and WEST).
    for (let i = 1; i < numOfLanes; i++) {
        // The y-coordinate of each dashed lane marking.
        const yCoord = topHorizontal + i * pixelWidthOfLane; 

        // Left-Sided lane markings (WEST) drawn before the intersection and crossing starts.
        canvas2D.beginPath();
        canvas2D.moveTo(0, yCoord);
        canvas2D.lineTo(leftVertical - widthOfPC, yCoord);
        canvas2D.stroke();

        // Right-Sided lane markings (EAST) drawn after the intersection and crossing ends.
        canvas2D.beginPath();
        canvas2D.moveTo(rightVertical + widthOfPC, yCoord);
        canvas2D.lineTo(junctionCanvas.width, yCoord);
        canvas2D.stroke();
    }

    // Below (CENTRE LINE) drawing dashed horizontal lane markings in white (EAST and WEST).
    for (let i = 1; i < numOfLanes; i++) {
        // The y-coordinate of each dashed lane marking.
        const yCoord = canvasY + i * pixelWidthOfLane; 

        // Ensures lane divider doesnt extend past bottom of the road boundary.
        if (yCoord < bottomHorizontal) {
            // Left-Sided lane markings (WEST) drawn before the intersection and crossing starts.
            canvas2D.beginPath();
            canvas2D.moveTo(0, yCoord);
            canvas2D.lineTo(leftVertical - widthOfPC, yCoord);
            canvas2D.stroke();

            // Right-Sided lane markings (EAST) drawn after the intersection and crossing ends.
            canvas2D.beginPath();
            canvas2D.moveTo(rightVertical + widthOfPC, yCoord);
            canvas2D.lineTo(junctionCanvas.width, yCoord);
            canvas2D.stroke();
        }
    }

    // Left of (CENTRE LINE) drawing dashed vertical lane markings in white (NORTH and SOUTH).
    for (let i = 1; i < numOfLanes; i++) {
        // The x-coordinate of each dashed lane marking.
        const xCoord = leftVertical + i * pixelWidthOfLane; 

        // Top-Sided lane markings (NORTH) drawn before the intersection and crossing starts.
        canvas2D.beginPath();
        canvas2D.moveTo(xCoord, 0);
        canvas2D.lineTo(xCoord, topHorizontal - widthOfPC);
        canvas2D.stroke();

        // Bottom-Sided lane markings (SOUTH) drawn after the intersection and crossing ends.
        canvas2D.beginPath();
        canvas2D.moveTo(xCoord, bottomHorizontal + widthOfPC);
        canvas2D.lineTo(xCoord, junctionCanvas.height);
        canvas2D.stroke();
    }

    // Right of (CENTRE LINE) drawing dashed vertical lane markings in white (NORTH and SOUTH).
    for (let i = 1; i < numOfLanes; i++) {
        // The x-coordinate of each dashed lane marking.
        const xCoord = canvasX + i * pixelWidthOfLane; 

        // Ensure lanes within boundary of road.
        if (xCoord < rightVertical) {
            // Top-Sided lane markings (NORTH) drawn before the intersection and crossing starts.
            canvas2D.beginPath();
            canvas2D.moveTo(xCoord, 0);
            canvas2D.lineTo(xCoord, topHorizontal - widthOfPC);
            canvas2D.stroke();

            // Bottom-Sided lane markings (SOUTH) drawn after the intersection and crossing ends.
            canvas2D.beginPath();
            canvas2D.moveTo(xCoord, bottomHorizontal + widthOfPC);
            canvas2D.lineTo(xCoord, junctionCanvas.height);
            canvas2D.stroke();
        }
    }

    // Horizontal Centre Line which is solid white to divide incoming and outgoing lanes.
    canvas2D.setLineDash([]);
    canvas2D.lineWidth = 3;

    // Left-Sided (WEST) solid white centre line drawn before intersection/crossing starts.
    canvas2D.beginPath();
    canvas2D.moveTo(0, canvasY);
    canvas2D.lineTo(leftVertical - widthOfPC, canvasY);
    canvas2D.stroke();

    // Right-Sided (EAST) solid white centre line drawn after intersection/crossing ends.
    canvas2D.beginPath();
    canvas2D.moveTo(rightVertical + widthOfPC, canvasY);
    canvas2D.lineTo(junctionCanvas.width, canvasY);
    canvas2D.stroke();

    // Top-Sided (NORTH) solid white centre line drawn before intersection/crossing starts.
    canvas2D.beginPath();
    canvas2D.moveTo(canvasX, 0);
    canvas2D.lineTo(canvasX, topHorizontal - widthOfPC);
    canvas2D.stroke();

    // Bottom-Sided (SOUTH) solid white centre line drawn after intersection/crossing ends.
    canvas2D.beginPath();
    canvas2D.moveTo(canvasX, bottomHorizontal + widthOfPC);
    canvas2D.lineTo(canvasX, junctionCanvas.height);
    canvas2D.stroke();
}

/**
 * Puffin crossing is drawn with stripes that are flowing opposite to direction of walking.
 * 
 * @param {number} topHorizontal : Y-coordinate of top of the edge of horizontal road.
 * @param {number} bottomHorizontal : Y-coordinate of bottom of the edge of the horizontal road.
 * @param {number} leftVertical : X-coordinate of left edge of the vertical road.
 * @param {number} rightVertical : X-coordinate of right edge of the vertical road.
 */
export function drawPuffinCrossing(topHorizontal, bottomHorizontal, leftVertical, rightVertical) {
    // Finds width of puffin crossing, so the road markings do not cross over into puffin crossing.
    const widthOfPC = puffinCrossingStripeLength();
  
    // Drawing of cross walk for top and bottom flowing vertically (NORTH and SOUTH).
    drawVertical(leftVertical, topHorizontal - widthOfPC, rightVertical - leftVertical, widthOfPC);
    drawVertical(leftVertical, bottomHorizontal, rightVertical - leftVertical, widthOfPC);
  
    // Drawing of cross walk for left and right flowing horizontally (EAST and WEST)
    drawHorizontal(leftVertical - widthOfPC, topHorizontal, widthOfPC, bottomHorizontal - topHorizontal);
    drawHorizontal(rightVertical, topHorizontal, widthOfPC, bottomHorizontal - topHorizontal);
}

/**
 * Drawing vertical crossing stripes for puffin crossing (NORTH and SOUTH).
 * 
 * @param {number} xCoord : x-coordinate where crossing begins.
 * @param {number} yCoord : y-coordinate where corssing begins.
 * @param {number} width : how wide the crossing is.
 * @param {number} height : how tall the crossing is.
 */
export function drawVertical(xCoord, yCoord, width, height) {
    // Save the current state of the canvas before modifying.
    canvas2D.save();
    canvas2D.beginPath();
    // Clipping area where stripes of puffin crossing drawn, rescricted within rectangle.
    canvas2D.rect(xCoord, yCoord, width, height);
    canvas2D.clip();

    let currentX = xCoord;
    // Loop until stripes drawn in entire restricted area.
    while (currentX < xCoord + width) {
        canvas2D.fillStyle = colourOfLaneMarking;
        canvas2D.fillRect(currentX, yCoord, pixelThicknessOfPC, height);
        currentX += pixelThicknessOfPC + pixelGapOfPCStripes;
    }
    // Restore the state of the canvas to prevent unintentional clipping elsewhere.
    canvas2D.restore();
}

/**
 * Drawing horizontal crossing stripes for puffin crossing (EAST and WEST).
 * 
 * @param {number} xCoord : x-coordinate where crossing begins.
 * @param {number} yCoord : y-coordinate where corssing begins.
 * @param {number} width : how wide the crossing is.
 * @param {number} height : how tall the crossing is.
 */
export function drawHorizontal(xCoord, yCoord, width, height) {
    // Save the current state of the canvas before modifying.
    canvas2D.save();
    canvas2D.beginPath();
    // Clipping area where stripes of puffin crossing drawn, rescricted within rectangle.
    canvas2D.rect(xCoord, yCoord, width, height);
    canvas2D.clip();

    let currentY = yCoord;
    // Loop until stripes drawn in entire restricted area.
    while (currentY < yCoord + height) {
        canvas2D.fillStyle = colourOfLaneMarking;
        canvas2D.fillRect(xCoord, currentY, width, pixelThicknessOfPC);
        currentY += pixelThicknessOfPC + pixelGapOfPCStripes;
    }
    // Restore the state of the canvas to prevent unintentional clipping elsewhere.
    canvas2D.restore();
}

// Draw the junction each time page loads and when input of lanes change.
inputNumOfLanes.addEventListener("input", junctionDrawing);
junctionDrawing();