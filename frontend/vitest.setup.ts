import "@testing-library/jest-dom/vitest";

HTMLCanvasElement.prototype.getContext = (() => ({
  clearRect: () => {},
  scale: () => {},
  beginPath: () => {},
  moveTo: () => {},
  lineTo: () => {},
  stroke: () => {},
})) as unknown as typeof HTMLCanvasElement.prototype.getContext;
