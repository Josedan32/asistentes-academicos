"use client";

import { useEffect, useRef, useState } from "react";

const CHARS_PER_TICK = 3;
const TICK_MS = 16;

export function useTypewriter(target: string, active: boolean): string {
  const [revealed, setRevealed] = useState(active ? "" : target);
  const targetRef = useRef(target);
  targetRef.current = target;

  useEffect(() => {
    if (!active) {
      setRevealed(target);
      return;
    }
    const id = setInterval(() => {
      setRevealed((prev) => {
        const full = targetRef.current;
        if (prev.length >= full.length) return prev;
        return full.slice(0, prev.length + CHARS_PER_TICK);
      });
    }, TICK_MS);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active]);

  return active ? revealed : target;
}
