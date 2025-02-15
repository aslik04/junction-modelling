/**
 * @fileoverview
 */

import {
    canvas2D, 
    puffinCrossingStripeLength, 
    getJunctionData
} from "./config.js";

import {
    pedestrianPngs
} from "./images.js";

/**
 * There are 4 puffin crossings in the simulation, one for each pedestrian cardinal direction. 
 * Where the top crossing is "north", bottom is "south", left is "west", right is "east". 
 * This simulates one pedestrian crossing from one end of the crossing to the other. 
 * The pedestrian always starts at the lefthand side of the road and walks to right hand side.
 * 
 * @param {string} direction : "north", "south", "west", "east".
 * @param {number} speed : How many pixels are covered in each stride (update).
 * @return {object} : An object which contains data about the pedestrian walking the crossing. 
 */
export function makePedestrian(direction, speed) {
    // To prevent repeated code utilised method with returns object of data regarding junction.
    const {numOfLanes,
        roadSize, 
        canvasX, 
        canvasY, 
        topHorizontal,
        bottomHorizontal,
        leftVertical,
        rightVertical
    } = getJunctionData();
    const widthOfPC = puffinCrossingStripeLength();
    
    // Initiliase an object which will store data of the pedestrian completing the crossing.
    let pedestrian = {};

    // Data about the pedestrians movemement in the simulation; speed, direction etc.
    pedestrian.direction = direction;
    pedestrian.speed = speed;

    // Data about the pedestrian size, where pedestrian is half the width of crossing.
    pedestrian.size = widthOfPC / 2;

    // Data to ensure frames pedestrian travels is tracked, and to see if crossing has been completed.
    pedestrian.completed = false;
    pedestrian.numOfFrames = 0;

    if (direction === "north") {
        // When completing the top ("north") crossing, we walk from right to left.
        pedestrian.x = rightVertical

        // Key part here is widthOfPC / 2, so we are in middle of pedestrian crossing.
        pedestrian.y = topHorizontal - widthOfPC / 2;
        
        // Speed set to negative as we are moving from right to left in simulation.
        pedestrian.dx = -speed;

        // For north crossing we are only changing the x coordinates so dy is set to 0.
        pedestrian.dy = 0;

        // Pedestrian walks across outgoing lane to incoming lane so right to left for north.
        pedestrian.start = rightVertical;
        pedestrian.end = leftVertical;

        // The amount of rotation need on the image so pedestrian faces forward while walking.
        pedestrian.rotate = -Math.PI / 2;
    } else if (direction === "east") {
        // Key part here is widthOfPC / 2, so we are in middle of pedestrian crossing
        pedestrian.x = rightVertical + widthOfPC / 2;

        // When completing the right ("east") crossing, we walk from down to up.
        pedestrian.y = bottomHorizontal;
        
        // For east crossing we are only changing the y coordinates so dx is set to 0
        pedestrian.dx = 0;

        // Speed set to negative as we are moving from down to up in simulation.
        pedestrian.dy = -speed;

        // Pedestrian walks across outgoing lane to incoming lane so down to up for east.
        pedestrian.start = bottomHorizontal;
        pedestrian.end = topHorizontal;

        // The amount of rotation need on the image so pedestrian faces forward while walking
        pedestrian.rotate = 0;
    } else if (direction === "south") {
        // When completing the bottom ("south") crossing, we walk from left to right.
        pedestrian.x = leftVertical

        // Key part here is widthOfPC / 2, so we are in middle of pedestrian crossing.
        pedestrian.y = bottomHorizontal + widthOfPC / 2;
        
        // Speed set to positive as we are moving from left to right in simulation.
        pedestrian.dx = speed;

        // For south crossing we are only changing the x coordinates so dy is set to 0
        pedestrian.dy = 0;

        // Pedestrian walks across outgoing lane to incoming lane so left to right for south.
        pedestrian.start = leftVertical;
        pedestrian.end = rightVertical;

        // The amount of rotation need on the image so pedestrian faces forward while walking
        pedestrian.rotate = Math.PI / 2;
    } else if (direction === "west") {
        // Key part here is widthOfPC / 2, so we are in middle of pedestrian crossing
        pedestrian.x = leftVertical - widthOfPC / 2;

        // When completing the left ("west") crossing, we walk from up to down.
        pedestrian.y = topHorizontal;
        
        // For west crossing we are only changing the y coordinates so dx is set to 0
        pedestrian.dx = 0;

        // Speed set to positive as we are moving from up to down in simulation.
        pedestrian.dy = speed;

        // Pedestrian walks across outgoing lane to incoming lane so up to down for west.
        pedestrian.start = topHorizontal;
        pedestrian.end = bottomHorizontal;

        // The amount of rotation need on the image so pedestrian faces forward while walking
        pedestrian.rotate = Math.PI;
    }

    // Return the object of pedestrian containing all relevant data to simulate the crossing.
    return pedestrian;
}

/**
 * Function which will update the pedestrians position to simulate walking, at stored speed.
 * If the pedestrian completes the crossing, they will disappear. 
 */
export function movePedestrian(pedestrian) {
    // If the pedestrian has completed the crossing do not update anymore.
    if (pedestrian.completed) {
        return;
    }

    // Updates the x and y coordinates by appending their horizontal and vertical speeds respectively.
    pedestrian.x += pedestrian.dx;
    pedestrian.y += pedestrian.dy;

    // In the case (dy = 0), this means we are moving horizontal, and only north and south crossings.
    if (pedestrian.dy === 0) {
        if (pedestrian.dx > 0) { // South bound crossing, left to right, as dx is positive.

            // If the pedestrian is within the boundaries of the crossing, update and increment frame count.
            if (pedestrian.x >= pedestrian.start && pedestrian.x <= pedestrian.end) {
                // Increment tracker for frame counter.
                pedestrian.numOfFrames++;
            }

            // If the pedestrian has reached the end of crossing, set completed variable to true.
            if (pedestrian.x > pedestrian.end) {
                pedestrian.completed = true;
            }
        } else if (pedestrian.dx < 0) { // North bound crossing right to left, as dx is negative.
            
            // If the pedestrian is within the boundaries of the crossing, update and increment frame count.
            if (pedestrian.x <= pedestrian.start && pedestrian.x >= pedestrian.end) {
                // Increment tracker for frame counter.
                pedestrian.numOfFrames++;
            }

            // If the pedestrian has reached the end of crossing, set completed variable to true.
            if (pedestrian.x < pedestrian.end) {
                pedestrian.completed = true;
            }
        }
    }

    // In the case (dx = 0), this means we are moving vertical, and only east and west crossings.
    if (pedestrian.dx === 0) {
        if (pedestrian.dy > 0) { // West bound crossing, up to down, as dy is positive.

            // If the pedestrian is within the boundaries of the crossing, update and increment frame count.
            if (pedestrian.y >= pedestrian.start && pedestrian.y <= pedestrian.end) {
                // Increment tracker for frame counter.
                pedestrian.numOfFrames++;
            }

            // If the pedestrian has reached the end of crossing, set completed variable to true.
            if (pedestrian.y > pedestrian.end) {
                pedestrian.completed = true;
            }
        } else if (pedestrian.dy < 0) { // East bound crossing down to up, as dy is negative.
            
            // If the pedestrian is within the boundaries of the crossing, update and increment frame count.
            if (pedestrian.y <= pedestrian.start && pedestrian.y >= pedestrian.end) {
                // Increment tracker for frame counter.
                pedestrian.numOfFrames++;
            }

            // If the pedestrian has reached the end set completed variable to true.
            if (pedestrian.y < pedestrian.end) {
                pedestrian.completed = true;
            }
        }
    }
}

/**
 * A function which will draw a pedestrian, using 3 pngs; start, walking1, walking2.
 * When at the beginning of crossing, end or waiting, the png is set to start.
 * When on the crossing, walking 1 and 2 are alternated every 10 frames to simulate walking to user.
 * If the pedestrian completes crossing, they will disappear and not be drawn.
 */
export function drawPedestrian(pedestrian) {
    // If the pedestrian has completed the crossing do not draw.
    if (pedestrian.completed) {
        return;
    }

    // Use a boolean flag, to track if the pedestrian is within the boundaries of the crossing. 
    let insideCrossing;

    // In the case (dy = 0), this means we are moving horizontal, and only north and south crossings.
    if (pedestrian.dy === 0) {

        // South bound crossing, left to right, as dx is positive.
        if (pedestrian.dx > 0) { 
            insideCrossing = (pedestrian.x >= pedestrian.start && pedestrian.x <= pedestrian.end);
        }

        // North bound crossing right to left, as dx is negative.
        if (pedestrian.dx < 0) { 
            insideCrossing = (pedestrian.x <= pedestrian.start && pedestrian.x >= pedestrian.end);
        }
    }

    // In the case (dx = 0), this means we are moving vertical, and only East and West crossings.
    if (pedestrian.dx === 0) {
        
        // West bound crossing, up to down, as dy is positive.
        if (pedestrian.dy > 0) { 
            insideCrossing = (pedestrian.y >= pedestrian.start && pedestrian.y <= pedestrian.end);
        }

        // East bound crossing down to up, as dy is negative.
        if (pedestrian.dy < 0) { 
            insideCrossing = (pedestrian.y <= pedestrian.start && pedestrian.y >= pedestrian.end);
        }
    }

    // Use a variable in order to store the png which is going to be drawn.
    let png;

    // If the pedestrian is currently not in the crossing we use the start image.
    if (!insideCrossing) {
        png = pedestrianPngs["start"];
    } else {
        // If the pedestrian is inside the crossing we alternate walking 1/2 png every 10 frames.
        if (Math.floor(pedestrian.numOfFrames / 10) % 2 === 0) {
            png = pedestrianPngs["walking1"];
        } else {
            png = pedestrianPngs["walking2"];
        }
    }

    // Make a checkpoint by saving canvas' current state, before applying transformation. 
    canvas2D.save();

    // Move the canvas' coordinates of the pedestrian to its current position. 
    canvas2D.translate(pedestrian.x, pedestrian.y);

    // Rotate the image, and then draw the png based on stored dimensions.
    canvas2D.rotate(pedestrian.rotate);
    canvas2D.drawImage(png, -pedestrian.size / 2, -pedestrian.size / 2, pedestrian.size, pedestrian.size);

    // Now restore the previous state of the canvas.
    canvas2D.restore();
}