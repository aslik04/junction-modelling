/**
 * @fileoverview This module is utilised to define functions that create, update and draw a forward moving vehicle. 
 * The position of the car is dependent on number of lanes, lane it is in and the dimensions of canvas. 
 * 
 * Dependencies:
 * - config.js: Used for the canvas element, the context we draw with, junction data and the lane data.
 * - images.js: Used for the png images of the car which are exported in an array.
 */

import {
    junctionCanvas, 
    canvas2D, 
    pixelWidthOfLane, 
    getJunctionData
} from "./config.js";

import {
    carPngs
} from "./images.js";

/**
 * Generates an object of a car which will move forward only, from any of the 4 cardinal directions.
 * All Cars are assumed to be lefthand drive, following normal U.K road Laws
 * A North bound car starts from bottom of the page and drives upwards. 
 * A South bound car starts from the top of the page and drives downwards. 
 * An East bound car starts from the left of the page and drives towards the right. 
 * A West bound car starts from the right of the page and drives towards the leftwards. 
 * 
 * @param {string} direction : The cardinal direction the car is driving (e.g., "NORTH").
 * @param {number} lane : The index of the lane car is travelling in (0 indexed, 0 to (inputNumOfLanes - 1)).
 * @param {number} speed : Speed of car, in amount of pixels covered per frame. 
 * @returns {Object} Object of car with properties: position (x, y), dimensions, speed, direction, and image.
 */
export function makeForwardCar(direction, lane, speed) {
    // To prevent repeated code utilised method with returns object of data regarding junction.
    const {topHorizontal, bottomHorizontal, leftVertical, rightVertical, widthOfCar, heightOfCar} = getJunctionData();
    
    // Initiliase an object which will store data of the car.
    let car = {};

    // Data about the direction car is heading in and the lane it is in. 
    car.direction = direction;
    car.indexOfLane = lane;
    
    // Metric data about the car including dimensions, speed etc.
    car.width = widthOfCar;
    car.height = heightOfCar;
    car.speed = speed;

    // Randomly select a png to represent this car object, this is just for variety in simulation.
    car.png = carPngs[Math.floor(Math.random() * carPngs.length)];

    // Dependent on the direction we want car to drive in, and its lane, the starting position of car is chosen.
    if (direction === "north") {
        car.x = leftVertical + pixelWidthOfLane / 2 + lane * pixelWidthOfLane;
        car.y = junctionCanvas.height + heightOfCar / 2;
    } else if (direction === "east") {
        car.x = -widthOfCar / 2;
        car.y = topHorizontal + pixelWidthOfLane / 2 + lane * pixelWidthOfLane;
    } else if (direction === "south") {
        car.x = rightVertical - pixelWidthOfLane / 2 - lane * pixelWidthOfLane;
        car.y = -heightOfCar / 2;
    } else if (direction === "west") {
        car.x = junctionCanvas.width + widthOfCar / 2;
        car.y = bottomHorizontal - pixelWidthOfLane / 2 - lane * pixelWidthOfLane;
    }

    // return the entire object of the car to then be used by future methods
    return car;
}

/**
 * Dynamically updates the car object as it is driving forward in a set direction. 
 * The travels a set number of pixels per update in its chosen direction. 
 * Utilises basic graphical math to move the cars pixels in the direction set. 
 * 
 * @param {Object} car : This is the object which we are updating.
 */
export function moveForwardCar(car) {
    if (car.direction === "north") {
        // Moves car upwards by decreasing y coordinate each update.
        car.y -= car.speed;

    } else if (car.direction === "east") {
        // Moves car right by increasing x coordinate each update.
        car.x += car.speed;

    } else if (car.direction === "south") {
        // Moves car downwards by increasing y coordinate each update.
        car.y += car.speed;

    } else if (car.direction === "west") {
        // Moves car left by decreasing x coordinate each update.
        car.x -= car.speed;

    }
}

/**
 * Draw the image of the car onto the canvas as a vehicle moving forward in one direction.
 * The image is centred in the x and y position of the car object.
 * 
 * @param {Object} car : This is the object of the car we are drawing.
 */
export function drawForwardCar(car) {
    // Make a checkpoint by saving canvas' current state. 
    canvas2D.save();

    // Move the canvas' coordinates ofr the car to its current position. 
    canvas2D.translate(car.x, car.y);

    // Angle we need to rotate png dependent on the direction of car
    let angle = 0;

    if (car.direction === "north") angle = 0;
    else if (car.direction === "east") angle = Math.PI / 2;
    else if (car.direction === "south") angle = Math.PI;
    else if (car.direction === "west") angle = -Math.PI / 2;

    // Rotate the image, and then draw the png based on stored dimensions.
    canvas2D.rotate(angle);
    canvas2D.drawImage(car.image, -car.width / 2, -car.height / 2, car.width, car.height);

    // Now restore the previous state of the canvas.
    canvas2D.restore();
}