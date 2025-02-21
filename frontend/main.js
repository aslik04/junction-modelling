import { junctionDrawing } from "./junction.js";
import { getJunctionData } from "./config.js"

/*==============================
  Canvas Resize
==============================*/
function updateCanvasSize() {
  const lanes = getJunctionData().numOfLanes;
  const middleSection = document.getElementById("junctionContainer");
  const canvas = document.getElementById("junctionCanvas");
  canvas.width = middleSection.clientWidth * (1 + (lanes / 10));
  canvas.height = middleSection.clientHeight * (1 + (lanes / 10));
}

window.addEventListener("load", () => {
  updateCanvasSize();
  junctionDrawing();
});
