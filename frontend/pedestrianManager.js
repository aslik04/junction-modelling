// pedestrianManager.js
import { makePedestrian, movePedestrian, drawPedestrian } from "./pedestrian.js";
import { getJunctionData } from "./config.js";

let activePedestrians = [];

/**
 * Spawn a pedestrian in a given direction.
 * Speed is computed so crossing takes ~2 seconds at 60 FPS.
 */
export function spawnPedestrian(direction) {
  const { leftVertical, rightVertical, topHorizontal, bottomHorizontal } = getJunctionData();
  let distance = (direction === "north" || direction === "south")
    ? Math.abs(rightVertical - leftVertical)
    : Math.abs(bottomHorizontal - topHorizontal);

  const speed = distance / 120; // ~2s at 60 FPS
  const ped = makePedestrian(direction, speed);
  activePedestrians.push(ped);
}

/**
 * Update all active pedestrians’ positions.
 */
export function updatePedestrians() {
  activePedestrians.forEach(p => movePedestrian(p));
  // Remove any that have finished crossing
  activePedestrians = activePedestrians.filter(p => !p.completed);
}

/**
 * Draw all active pedestrians.
 */
export function drawPedestrians() {
  activePedestrians.forEach(p => drawPedestrian(p));
}
