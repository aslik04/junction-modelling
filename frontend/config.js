/**
 * @constant {HTMLCanvasElement} junctionCanvas : The canvas where the junction is drawn.
 */
export const junctionCanvas = document.getElementById("junctionCanvas");

/**
 * @constant {CanvasRenderingContext2D} canvas2D : Context of the canvas, which gives methods in order to draw shapes, lines and images in our 2D canvas. 
 *                                                 This provides an interface for our drawing operations to act on the canvas.
 */
export const canvas2D = junctionCanvas.getContext("2d");

/**
 * @constant {HTMLInputElement} inputNumOfLanes : Amount of lanes user has inputted per direction (1 - 5).
 */
export const inputNumOfLanes = document.getElementById("laneInputNum");

/**
 * @constant {number} pixelWidthOfLane : How many pixels wide each lane in the junction is.
 */
export const pixelWidthOfLane = 30;

/**
 * @constant {number} pixelThicknessOfPC : How many pixels thick each stripe in a puffin crossing is.
 */
export const pixelThicknessOfPC = 6;

/**
 * @constant {number} pixelGapOfPCStripes : How much pixels gap there is between each stripe in a puffin crossing.
 */
export const pixelGapOfPCStripes = 3;

/**
 * @constant {string} colourOfRoad : What colour the road of the junction is.
 */
export const colourOfRoad = "#666666";

/**
 * @constant {string} colourOfLaneMarking : White colour for the lane markings on the road.
 */
export const colourOfLaneMarking = "#ffffff";

/**
 * @constant {string} colourOfBackground : Green colour for the background of Website
 */
export const colourOfBackground = "#86b049";

/**
 * Returns how many pixels long a short stripe is, (utilised for puffin crossing). 
 * To ensure lane markings do not cross over puffin crossing.
 * Defined as being twice the width of a lane (arbitrary).
 * 
 * @returns {number} : How many pixels long a short stripe should be.
 */
export function puffinCrossingStripeLength() {
    return pixelWidthOfLane * 2;
}

/**
 * Calculates data representing the junction according to user input lanes, and returns this data as an object.
 * Data includes the size of the road, centre of canvas, road boundaries, and dimensions of the car.
 *
 * @returns {Object} An object containing:
 *   - roadSize {number} : The total size of the road for incoming and outgoing traffic (in pixels).
 *   - canvasX {number} : The x-coordinate of the centre of the canvas.
 *   - canvasY {number} : The y-coordinate of the centre of the canvas.
 *   - topHorizontal {number} : The y-coordinate corresponding to the top boundary of the road.
 *   - bottomHorizontal {number} : The y-coordinate corresponding to the bottom boundary of the road.
 *   - leftVertical {number} : The x-coordinate corresponding to the left boundary of the road.
 *   - rightVertical {number} : The x-coordinatecorresponding to the right boundary of the road.
 *   - widthOfCar {number} : The width of a car (80% of lane width).
 *   - heightOfCar {number} : The height of a car (2 times lane width).
 */
export function getJunctionData() {
    // Parses the input given by user to ensure it is a valid whole number (1 - 5).
    const numOfLanes = parseInt(inputNumOfLanes.value, 10);

    // User input invalid not between (1 - 5), or input is not a whole number.
    if (numOfLanes < 1 || numOfLanes > 5 || isNaN(numOfLanes)) {
        return;
    }

    // The total size of the road, incoming and outgoing lanes included.
    const roadSize = 2 * numOfLanes * pixelWidthOfLane;

    // Centre (x, y) coordinates of the canvas.
    const canvasX = junctionCanvas.width / 2;
    const canvasY = junctionCanvas.height / 2;

    // Boundaries of road for all 4 cardinal directions.
    const topHorizontal = canvasY - roadSize / 2;
    const bottomHorizontal = canvasY + roadSize / 2;
    const leftVertical = canvasX - roadSize / 2;
    const rightVertical = canvasX + roadSize / 2;

    // The dimensions of the car, which will be scaled according the number of lanes input.
    const widthOfCar = pixelWidthOfLane * 0.8;
    const heightOfCar = pixelWidthOfLane * 2;

    return {
        roadSize, 
        canvasX, 
        canvasY, 
        topHorizontal,
        bottomHorizontal,
        leftVertical,
        rightVertical,
        widthOfCar,
        heightOfCar
    };
}