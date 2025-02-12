/**
 * @constant {HTMLCanvasElement} junctionCanvas : The canvas where the junction is drawn.
 */
const junctionCanvas = document.getElementById("junctionCanvas");

/**
 * @constant {CanvasRenderingContext2D} canvas2D : Context of the canvas, which gives methods in order to draw shapes, lines and images in our 2D canvas. 
 *                                                 This provides an interface for our drawing operations to act on the canvas.
 */
const canvas2D = junctionCanvas.getContext("2d");

/**
 * @constant {HTMLInputElement} inputNumOfLanes : Amount of lanes user has inputted per direction (1 - 5).
 */
const inputNumOfLanes = document.getElementById("laneInputNum");

/**
 * @constant {number} pixelWidthOfLane : How many pixels wide each lane in the junction is.
 */
const pixelWidthOfLane = 30;

/**
 * @constant {number} pixelThicknessOfPC : How many pixels thick each stripe in a puffin crossing is.
 */
const pixelThicknessOfPC = 6;

/**
 * @constant {number} pixelGapOfPCStripes : How much pixels gap there is between each stripe in a puffin crossing.
 */
const pixelGapOfPCStripes = 3;

/**
 * @constant {string} colourOfRoad : What colour the road of the junction is.
 */
const colourOfRoad = "#666666";

/**
 * @constant {string} colourOfLaneMarking : White colour for the lane markings on the road.
 */
const colourOfLaneMarking = "#ffffff";

/**
 * @constant {string} colourOfBackground : Green colour for the background of Website
 */
const colourOfBackground = "#86b049";

/**
 * @constant {HTMLInputElement} inputVPHNorth : Amount of vehicles per hour incoming from North.
 */
const inputVPHNorth = document.getElementById("VPHNorth");

/**
 * @constant {HTMLInputElement} inputVPHEast : Amount of vehicles per hour incoming from East.
 */
const inputVPHEast = document.getElementById("VPHEast");

/**
 * @constant {HTMLInputElement} inputVPHSouth : Amount of vehicles per hour incoming from South.
 */
const inputVPHSouth = document.getElementById("VPHSouth");

/**
 * @constant {HTMLInputElement} inputVPHWest : Amount of vehicles per hour incoming from West.
 */
const inputVPHWest = document.getElementById("VPHWest");

/**
 * @constant {HTMLSelectElement} inputBusLane : Does User want to include bus lane yes or no.
 */
const inputBusLane = document.getElementById("busLane");

/**
 * @constant {HTMLInputElement} inputPedestriansNorth : Amount of pedestrians per hour incoming from North.
 */
const inputPedestriansNorth = document.getElementById("pedestriansNorth");

/**
 * @constant {HTMLInputElement} inputPedestriansEast : Amount of pedestrians per hour incoming from East.
 */
const inputPedestriansEast = document.getElementById("pedestriansEast");

/**
 * @constant {HTMLInputElement} inputPedestriansSouth : Amount of pedestrians per hour incoming from South.
 */
const inputPedestriansSouth = document.getElementById("pedestriansSouth");

/**
 * @constant {HTMLInputElement} inputPedestriansWest : Amount of pedestrians per hour incoming from West.
 */
const inputPedestriansWest = document.getElementById("pedestriansWest");


/**
 * Returns how many pixels long a short stripe is, (utilised for puffin crossing). 
 * To ensure lane markings do not cross over puffin crossing.
 * Defined as being twice the width of a lane (arbitrary).
 * 
 * @returns {number} : How many pixels long a short stripe should be.
 */
function puffinCrossingStripeLength() {
    return pixelWidthOfLane * 2;
}

/**
 * Main method which renders the entire junction, by utilising helper methods detailed by file. 
 * Draws all roads, lanes, puffin crossings of the entire 4 way junction using predefined colours. 
 * Canvas is cleared and each element of the junction is drawn based on user input.
 */
function junctionDrawing() {
    // Parses the input given by user to ensure it is a valid whole number (1 - 5).
    const numOfLanes = parseInt(inputNumOfLanes.value, 10);

    // User input invalid not between (1 - 5), or input is not a whole number.
    if (numOfLanes < 1 || numOfLanes > 5 || isNaN(numOfLanes)) {
        return;
    }

    // Clears and fills the canvas with a green colour for background.
    canvas2D.fillStyle = colourOfBackground;
    canvas2D.fillRect(0, 0, junctionCanvas.width, junctionCanvas.height);

    // Number of pixels for each road, based on user inputs and multiplied by two for incoming/outgoing.
    const roadSize = 2 * numOfLanes * pixelWidthOfLane;
    
    // centreed coordinates for the canvas.
    const canvasX = junctionCanvas.width / 2;
    const canvasY = junctionCanvas.height / 2;

    // Boundaries of road for all 4 cardinal directions.
    const topHorizontal = canvasY - roadSize / 2;
    const bottomHorizontal = canvasY + roadSize / 2;
    const leftVertical = canvasX - roadSize / 2;
    const rightVertical = canvasX + roadSize / 2;

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
function drawLanes(numOfLanes, topHorizontal, bottomHorizontal, leftVertical, rightVertical, canvasX, canvasY) {
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
function drawPuffinCrossing(topHorizontal, bottomHorizontal, leftVertical, rightVertical) {
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
function drawVertical(xCoord, yCoord, width, height) {
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
function drawHorizontal(xCoord, yCoord, width, height) {
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