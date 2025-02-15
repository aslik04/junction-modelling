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
 * @constant {HTMLInputElement} inputVPHNorth : Amount of vehicles per hour incoming from North.
 */
export const inputVPHNorth = document.getElementById("VPHNorth");

/**
 * @constant {HTMLInputElement} inputVPHEast : Amount of vehicles per hour incoming from East.
 */
export const inputVPHEast = document.getElementById("VPHEast");

/**
 * @constant {HTMLInputElement} inputVPHSouth : Amount of vehicles per hour incoming from South.
 */
export const inputVPHSouth = document.getElementById("VPHSouth");

/**
 * @constant {HTMLInputElement} inputVPHWest : Amount of vehicles per hour incoming from West.
 */
export const inputVPHWest = document.getElementById("VPHWest");

/**
 * @constant {HTMLSelectElement} inputBusLane : Does User want to include bus lane yes or no.
 */
export const inputBusLane = document.getElementById("busLane");

/**
 * @constant {HTMLInputElement} inputPedestriansNorth : Amount of pedestrians per hour incoming from North.
 */
export const inputPedestriansNorth = document.getElementById("pedestriansNorth");

/**
 * @constant {HTMLInputElement} inputPedestriansEast : Amount of pedestrians per hour incoming from East.
 */
export const inputPedestriansEast = document.getElementById("pedestriansEast");

/**
 * @constant {HTMLInputElement} inputPedestriansSouth : Amount of pedestrians per hour incoming from South.
 */
export const inputPedestriansSouth = document.getElementById("pedestriansSouth");

/**
 * @constant {HTMLInputElement} inputPedestriansWest : Amount of pedestrians per hour incoming from West.
 */
export const inputPedestriansWest = document.getElementById("pedestriansWest");

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