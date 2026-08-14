import { createRef } from "react";
import { act, fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ScratchCanvas, type ScratchCanvasHandle } from "./ScratchCanvas";

describe("ScratchCanvas", () => {
  it("shows the clear button only after drawing starts", () => {
    render(<ScratchCanvas />);
    expect(screen.queryByLabelText(/borrar tablero/i)).not.toBeInTheDocument();

    const canvas = document.querySelector("canvas") as HTMLCanvasElement;
    fireEvent.pointerDown(canvas, { clientX: 0, clientY: 0 });
    fireEvent.pointerMove(canvas, { clientX: 10, clientY: 10 });

    expect(screen.getByLabelText(/borrar tablero/i)).toBeInTheDocument();
  });

  it("clicking borrar hides the button again", () => {
    render(<ScratchCanvas />);
    const canvas = document.querySelector("canvas") as HTMLCanvasElement;
    fireEvent.pointerDown(canvas, { clientX: 0, clientY: 0 });
    fireEvent.pointerMove(canvas, { clientX: 10, clientY: 10 });

    fireEvent.click(screen.getByLabelText(/borrar tablero/i));

    expect(screen.queryByLabelText(/borrar tablero/i)).not.toBeInTheDocument();
  });

  it("exposes an imperative clear() that resets the drawn state", () => {
    const ref = createRef<ScratchCanvasHandle>();
    render(<ScratchCanvas ref={ref} />);
    const canvas = document.querySelector("canvas") as HTMLCanvasElement;
    fireEvent.pointerDown(canvas, { clientX: 0, clientY: 0 });
    fireEvent.pointerMove(canvas, { clientX: 10, clientY: 10 });
    expect(screen.getByLabelText(/borrar tablero/i)).toBeInTheDocument();

    act(() => ref.current?.clear());

    expect(screen.queryByLabelText(/borrar tablero/i)).not.toBeInTheDocument();
  });
});
