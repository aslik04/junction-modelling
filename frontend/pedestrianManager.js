/**
 * @fileoverview This file is for managing the spawning, updating of pedestrians in the simulation. 
 * Currently, pedestrians are spawned at all 4 directions at the same time, and move at the same time.
 * However, the foundation is there to allow for pedestrians to be spawned at different times and move at different times.
 *
 * Features:
 * - We create new pedestrians based on direction and we dynamically calculated speed.
 * - We update pedestrian positions and removes those that have completed crossing.
 * - We draw pedestrians at their current positions using predefined images.
 * - We retrieve the users input for pedestrian crossing duration.
 *
 * Dependencies:
 * - pedestrian.js: Provides pedestrian creation, movement, and drawing functions.
 * - config.js: Supplies junction dimensions for proper pedestrian positioning.
 */

import { 
  makePedestrian, 
  movePedestrian, 
  drawPedestrian 
} from "./pedestrian.js";

import { 
  getJunctionData 
} from "./config.js";

// We utilise an array in order to track the active pedestrians.
// Which allows us to update and draw them all in one go.
let activePedestrians = [];

/**
 * This function currently is only used to generate a pedestrian at all 4 directions at the same time.
 * However, we did think of making pedestrian directions configurable, but we decided against it due to scope.
 * Despite this the existing foundation allows for this to be implemented in the future.
 * 
 * - We calculate the distance the pedestrian needs to travel.
 * - We calculate the speed the pedestrian needs to travel at.
 * - We create a pedestrian object, storing all the relevant data.
 * 
 * @param {string} direction - The cardinal direction of the crossing ("north", "south", "west", "east").
 */
export function spawnPedestrian(direction) {
  // Retreive the junction data
  const { 
    leftVertical, 
    rightVertical, 
    topHorizontal, 
    bottomHorizontal 
  } = getJunctionData();

  // The number of frames per second
  const fps = 60;

  // The duration of the pedestrian crossing set by the user, or 0 if not set.
  const pedestrianDuration = parseInt(localStorage.getItem("pedestrianDuration"), 10) || 0;

  // Utilised for debugging, to ensure users input is read correctly.
  console.log(pedestrianDuration);

  // Calculate the distance the pedestrian needs to travel.
  let distance = (direction === "north" || direction === "south")
    ? Math.abs(rightVertical - leftVertical) // Horizontal distance
    : Math.abs(bottomHorizontal - topHorizontal); // Vertical distance

  // Computation of the pixels travelled per frame.
  const speed = distance / (fps * pedestrianDuration);

  // Gennerate an object for this pedestrian
  const ped = makePedestrian(direction, speed);

  // Add the pedestrian to the active pedestrians array
  activePedestrians.push(ped);
}

/**
 * We update all of the active pedestrians' positions, this currently is for all 4 directions,
 * once they complete journey at same time they are removed from the array.
 * 
 * - Moves each pedestrian by updating their position based on speed and direction.
 * - Removes pedestrians from the active list once they have completed the crossing.
 */
export function updatePedestrians() {
  // Move all active pedestrians, which in our scope is all 4 directions simultaneously.
  activePedestrians.forEach(p => movePedestrian(p));

  // Filter out all pedestrians that have completed their journey.
  activePedestrians = activePedestrians.filter(p => !p.completed);
}

/**
 * Draws all active pedestrians, which in our scope is all 4 directions simultaneously.
 * 
 * - Iterates over the activePedestrians array and renders each pedestrian at its current position.
 */
export function drawPedestrians() {
  activePedestrians.forEach(p => drawPedestrian(p));
}