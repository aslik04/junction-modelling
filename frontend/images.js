/**
 * @fileoverview This module is used to load any images related to the junction. 
 * These images are stored in variables which can be exported to various other modules. 
 * The images are converted into @type {HTMLImageElement[]} arrays, which are then used in simulation. 
 */

/**
 * Initialise an empty array, which will store pngs of cars.
 * 
 * @type {HTMLImageElement[]}
 */
export const carPngs = [];

/**
 * Method which loads png of cars from folder "cars", that have a list of predefined names. 
 * These png are loaded one by one into the {@link carPngs} array.
 * 
 * @returns {void}
 */
export function loadCarPngs() {
    // The list of cars from our selection of images
    const fileNames = ["redCar", "greenCar", "yellowCar", "purpleCar", "blueCar"];

    // Looping through the entire array of cars
    fileNames.forEach(name => {
        const png = new Image();
        png.src = `cars/${name}.png`;
        carPngs.push(png);
    });
}

/**
 * Initialise an empty array, which will store pngs of pedestrian.
 * 
 * @type {HTMLImageElement[]}
 */
export const pedestrianPngs = [];

/**
 * Method which loads png of cars from folder "pedestrian", that have a list of predefined names. 
 * These png are loaded one by one into the {@link pedestrianPngs} array.
 * Three png used, designed in sequence so pedestrian animation simulates walking.
 * 
 * @returns {void}
 */
export function loadPedestrianPngs() {
    const fileNames = ["start", "walking1", "walking2"];
    fileNames.forEach(name => {
      const img = new Image();
      // The key is to use /static/pedestrian/ so it fetches from the server.
      img.src = `/static/pedestrian/${name}.png`;
      img.onload = () => console.log(`Loaded pedestrian image: ${name}`);
      img.onerror = () => console.error(`Failed to load pedestrian image: ${name}`);
      pedestrianPngs.push(img);
    });
  }