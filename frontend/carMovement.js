/**
 * @fileoverview This module is utilised to define functions that create, update and draw a left turn, forward, and right turn vehicle. 
 * The position of the car is dependent on the direction travelling, speed, and the dimensions of canvas. 
 * The left turns are always from left most lane, (index 0 lane), although this could be modified to allow other lanes.
 * Also define functions that create, update and draw a forward moving vehicle. 
 * The position of the car is dependent on number of lanes, lane it is in and the dimensions of canvas. 
 * The right turns are always from right most lane, (index numOfLane - 1), although this could be modified to allow other lanes.
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
 * Generates an object of a car which will move forward, left or right, from any of the 4 cardinal directions.
 * All Cars are assumed to be lefthand drive, following normal U.K road Laws, 
 * and left turns always start/end in lane 0, and right turns start/end in numOfLanes - 1 (rightmost lane).
 * A North bound car starts from bottom of the page and drives upwards, 
 *  if turning left, once reaching start of junction turns left into west bound,
 *  if turning right, once reaching start of junction turns right into east bound. 
 * A South bound car starts from the top of the page and drives downwards, 
 *  if turning left, once reaching start of junction turns left into east bound, 
 *  if turning right, once reaching start of junction turns right into west bound. 
 * An East bound car starts from the left of the page and drives towards the right, 
 *  if turning left, once reaching start of junction turns left into south bound, 
 *  if turning right, once reaching start of junction turns right into north bound. 
 * A West bound car starts from the right of the page and drives towards the leftwards, 
 *  if turning left, once reaching start of junction turns left into north bound, 
 *  if turning right, once reaching start of junction turns right into south bound. 
 * 
 * @param {string} direction : The cardinal direction the car is driving (e.g., "NORTH").
 * @param {number} lane : The index of the lane car is travelling in (0 indexed, 0 to (inputNumOfLanes - 1)).
 * @param {number} speed : Speed of car, in amount of pixels covered per frame. 
 * @param {string} typeOfTurn : Can be "left" or "right" (to select the starting lane).
 * @returns {Object} Object of car with properties: position (x, y), dimensions, speed, direction, and image.
 */
export function makeCar(direction, lane, speed, typeOfTurn) {
    // To prevent repeated code utilised method with returns object of data regarding junction.
    const {
        numOfLanes,
        topHorizontal, 
        bottomHorizontal, 
        leftVertical, 
        rightVertical, 
        widthOfCar, 
        heightOfCar
    } = getJunctionData();

    // Based on the type of turn we override the, lane index, to 0 for left, and (numOfLanes - 1) for right.
    if (typeOfTurn === "left") {
        lane = 0;
    } else if (typeOfTurn === "right") {
        lane = numOfLanes - 1;
    } else if (typeOfTurn !== "forward") {
        throw new Error("Invalid type of turn: " + typeOfTurn);
    }
    
    // Initiliase an object which will store data of the car.
    let car = {};

    // Randomly select a png to represent this car object, this is just for variety in simulation.
    car.png = carPngs[Math.floor(Math.random() * carPngs.length)];

    // Dependent on the direction we want car to drive in, the starting position of car is chosen.
    if (direction === "north") {
        car.x = leftVertical + pixelWidthOfLane / 2 + lane * pixelWidthOfLane;
        car.y = junctionCanvas.height + heightOfCar / 2;

        // Initial angle of the car for right turns.
        car.rightTurnInitialAngle = 0;
    } else if (direction === "east") {
        car.x = -widthOfCar / 2;
        car.y = topHorizontal + pixelWidthOfLane / 2 + lane * pixelWidthOfLane;

        // Initial angle of the car for right turns.
        car.rightTurnInitialAngle = Math.PI / 2;
    } else if (direction === "south") {
        car.x = rightVertical - pixelWidthOfLane / 2 - lane * pixelWidthOfLane;
        car.y = -heightOfCar / 2;

        // Initial angle of the car for right turns.
        car.rightTurnInitialAngle = Math.PI;
    } else if (direction === "west") {
        car.x = junctionCanvas.width + widthOfCar / 2;
        car.y = bottomHorizontal - pixelWidthOfLane / 2 - lane * pixelWidthOfLane;

        // Initial angle of the car for right turns.
        car.rightTurnInitialAngle = -Math.PI / 2;
    }

    // Data about the direction car is heading in and the lane it is in. 
    car.direction = direction;
    car.indexOfLane = lane;

    // Tracker to check if the car has completed its left turn.
    car.completedLeft = false;

    // Tracker for phase of right turn, 0 (before junction), 1 (during junction) or 2 (after junction).
    car.rightTurnPhase = 0;
    
    // Metric data about the car including dimensions, speed etc.
    car.width = widthOfCar;
    car.height = heightOfCar;
    car.speed = speed;
    car.currentRightTurnAngle = car.rightTurnInitialAngle

    // Store the type of turn used.
    car.typeOfTurn = typeOfTurn;

    // return the entire object of the car to then be used by future methods
    return car;
}

/**
 * Draw the image of the car onto the canvas as a vehicle completing its movement.
 * The image is centred in the x and y position of the car object.
 * 
 * @param {Object} car : This is the object of the car we are drawing.
 */
export function drawCar(car) {
    // Make a checkpoint by saving canvas' current state. 
    canvas2D.save();

    // Move the canvas' coordinates ofr the car to its current position. 
    canvas2D.translate(car.x, car.y);

    // Angle we need to rotate png dependent on the direction of car
    let angle = 0;

    if (car.typeOfTurn === "right") {

        // When a car is turning right we need to dynamically update the cars angle.
        angle = car.currentRightTurnAngle;
    } else { // Otherwise we rotate car based on angle from cars current direction.
        if (car.direction === "north") angle = 0;
        else if (car.direction === "east") angle = Math.PI / 2;
        else if (car.direction === "south") angle = Math.PI;
        else if (car.direction === "west") angle = -Math.PI / 2;
    }

    // Rotate the image, and then draw the png based on stored dimensions.
    canvas2D.rotate(angle);
    canvas2D.drawImage(car.png, -car.width / 2, -car.height / 2, car.width, car.height);

    // Now restore the previous state of the canvas.
    canvas2D.restore();
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
 * Dynamically updates the car object as it is driving forward in a set direction, 
 * then once it reaches the start of junction turns left in correct lane. 
 * When the boundary is reach it turns 90 degrees anticlockwise to face direction after left turn.
 * The travels a set number of pixels per update in its chosen direction. 
 * Utilises basic graphical math to move the cars pixels in the direction set. 
 * 
 * @param {Object} car : This is the object which we are updating.
 */
export function moveLeftTurnCar(car) {
    // To prevent repeated code utilised method with returns object of data regarding junction.
    const {
        topHorizontal, 
        bottomHorizontal, 
        leftVertical, 
        rightVertical, 
    } = getJunctionData();

    // Margin used to normal boundaries so car can turn before reach an edge.
    const margin = 15;

    // If the car hasnt completed its left turn we need to update according to its position in canvas.
    if (!car.completedLeft) {
        if (car.direction === "north") {

            // When moving North, we keep decreasing y till we reach the bottom boundary and margin.
            if (car.y - car.speed <= bottomHorizontal - margin) {
                car.y = bottomHorizontal - margin;
                car.direction = "west";
                car.completedLeft = true;
            } else {
                // Moves car upwards by decreasing y coordinate each update, and move north.
                car.y -= car.speed;
            }
        } else if (car.direction === "east") {

            // When moving East, we keep increasing x till we reach the left boundary and margin.
            if (car.x + car.speed >= leftVertical + margin) {
                car.x = leftVertical + margin;
                car.direction = "north";
                car.completedLeft = true;
            } else {
                // Moves car right by increasing x coordinate each update, and move east.
                car.x += car.speed;
            }
        } else if (car.direction === "south") {

            // When moving South, we keep increasing y till we reach the top boundary and margin.
            if (car.y + car.speed >= topHorizontal + margin) {
                car.y = topHorizontal + margin;
                car.direction = "east";
                car.completedLeft = true;
            } else {
                // Moves car downwards by increasing y coordinate each update, and move south.
                car.y += car.speed;
            }
        } else if (car.direction === "west") {

            // When moving West, we keep dcereasing x till we reach the right boundary and margin.
            if (car.x - car.speed <= rightVertical + margin) {
                car.x = rightVertical - margin;
                car.direction = "south";
                car.completedLeft = true;
            } else {
                // Moves car left by decreasing x coordinate each update, and move west.
                car.x -= car.speed;
            }
        }
    } else {
        // Once the turns complete just keep moving forward.
        moveForwardCar(car);
    }
}

/**
 * Dynamically updates the car object as it is driving forward in a set direction, 
 * then once it reaches first boundary (start of junction) turns 45 degrees right towards correct lane, 
 * once it reaches second boundary turns another 45 degrees towards correct lane.
 * The travels a set number of pixels per update in its chosen direction. 
 * Utilises basic graphical math to move the cars pixels in the direction set. 
 * 
 * @param {Object} car : This is the object which we are updating.
 */
export function moveRightTurnCar(car) {
    // To prevent repeated code utilised method with returns object of data regarding junction.
    const {
        topHorizontal, 
        bottomHorizontal, 
        leftVertical, 
        rightVertical, 
    } = getJunctionData();

    // Margin used to normal boundaries so car can turn before reach an edge.
    const margin = 15;

    // Position of car during right turn updated using current angle.
    // dx = speed * sin(angle).
    car.x += car.speed * Math.sin(car.currentRightTurnAngle);
    // dy = -speed * cos(angle).
    car.y += -car.speed * Math.cos(car.currentRightTurnAngle);

    // If the car is in phase 0, and hasnt reach start of junction yet just keep going forward.
    if (car.rightTurnPhase === 0) {
        if (car.direction === "north") {

            // When moving North, we keep decreasing y till we reach the bottom boundary and margin.
            if (car.y - car.speed <= bottomHorizontal - margin) {
                car.y = bottomHorizontal - margin;

                // Reached start of junction so now phase 1 starts, and car turned 45 degrees.
                car.rightTurnPhase = 1;
                car.currentRightTurnAngle = car.rightTurnInitialAngle + Math.PI / 4;
            }
        } else if (car.direction === "east") {

            // When moving East, we keep increasing x till we reach the left boundary and margin.
            if (car.x + car.speed >= leftVertical + margin) {
                car.x = leftVertical + margin;

                // Reached start of junction so now phase 1 starts, and car turned 45 degrees.
                car.rightTurnPhase = 1;
                car.currentRightTurnAngle = car.rightTurnInitialAngle + Math.PI / 4;
            } 
        } else if (car.direction === "south") {

            // When moving South, we keep increasing y till we reach the top boundary and margin.
            if (car.y + car.speed >= topHorizontal + margin) {
                car.y = topHorizontal + margin;

                // Reached start of junction so now phase 1 starts, and car turned 45 degrees.
                car.rightTurnPhase = 1;
                car.currentRightTurnAngle = car.rightTurnInitialAngle + Math.PI / 4;
            }
        } else if (car.direction === "west") {

            // When moving West, we keep dcereasing x till we reach the right boundary and margin.
            if (car.x - car.speed <= rightVertical + margin) {
                car.x = rightVertical + margin;

                // Reached start of junction so now phase 1 starts, and car turned 45 degrees.
                car.rightTurnPhase = 1;
                car.currentRightTurnAngle = car.rightTurnInitialAngle + Math.PI / 4;
            }
        }
    } else if (car.rightTurnPhase === 1) { // We are inside the junction turning 45 degrees towards middle.
        if (car.direction === "north") {
            
            // If we reach second boundary (middle of junction) where right incoming lane is, we move to phase 2.
            if (car.x >= rightVertical - margin) {

                // Car has left junction now in phase 2, and is now facing East.
                car.rightTurnPhase = 2;
                car.currentRightTurnAngle = car.rightTurnInitialAngle + Math.PI / 2;
            }
        } else if (car.direction === "east") {
            
            // If we reach second boundary (middle of junction) where right incoming lane is, we move to phase 2.
            if (car.y >= bottomHorizontal - margin) {

                // Car has left junction now in phase 2, and is now facing South.
                car.rightTurnPhase = 2;
                car.currentRightTurnAngle = car.rightTurnInitialAngle + Math.PI / 2;
            }
        } else if (car.direction === "south") {
            
            // If we reach second boundary (middle of junction) where right incoming lane is, we move to phase 2.
            if (car.x <= leftVertical + margin) {

                // Car has left junction now in phase 2, and is now facing West.
                car.rightTurnPhase = 2;
                car.currentRightTurnAngle = car.rightTurnInitialAngle + Math.PI / 2;
            }
        } else if (car.direction === "west") {
            
            // If we reach second boundary (middle of junction) where right incoming lane is, we move to phase 2.
            if (car.y <= topHorizontal + margin) {

                // Car has left junction now in phase 2, and is now facing North.
                car.rightTurnPhase = 2;
                car.currentRightTurnAngle = car.rightTurnInitialAngle + Math.PI / 2;
            }
        }
    }
}