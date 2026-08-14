import "@testing-library/jest-dom/vitest";

// jsdom does not implement canvas rendering; stub just enough of the 2D context API for
// components (e.g. ScratchCanvas) that draw on mount/interaction without crashing tests.
HTMLCanvasElement.prototype.getContext = (() => ({
  clearRect: () => {},
  scale: () => {},
  beginPath: () => {},
  moveTo: () => {},
  lineTo: () => {},
  stroke: () => {},
})) as unknown as typeof HTMLCanvasElement.prototype.getContext;
