import { useEffect, useState, useRef } from "react";

function parseTarget(value: string): { target: number; decimals: number; prefix: string; suffix: string } {
  const cleaned = value.replace(/,/g, "");
  const match = cleaned.match(/^([^\d]*)(\d+\.?\d*)([^\d]*)$/);
  if (!match) return { target: 0, decimals: 0, prefix: "", suffix: "" };
  const num = parseFloat(match[2]);
  const decimals = match[2].includes(".") ? match[2].split(".")[1].length : 0;
  return { target: num, decimals, prefix: match[1], suffix: match[3] };
}

function formatWithCommas(n: number, decimals: number): string {
  const fixed = n.toFixed(decimals);
  const [intPart, decPart] = fixed.split(".");
  const withCommas = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  return decPart ? `${withCommas}.${decPart}` : withCommas;
}

export function useCountUp(value: string, duration = 1200) {
  const { target, decimals, prefix, suffix } = parseTarget(value);
  const [display, setDisplay] = useState(`${prefix}${formatWithCommas(0, decimals)}${suffix}`);
  const frameRef = useRef<number>();

  useEffect(() => {
    const start = performance.now();

    const step = (now: number) => {
      const progress = Math.min((now - start) / duration, 1);
      // ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = eased * target;
      setDisplay(`${prefix}${formatWithCommas(current, decimals)}${suffix}`);
      if (progress < 1) {
        frameRef.current = requestAnimationFrame(step);
      }
    };

    frameRef.current = requestAnimationFrame(step);
    return () => { if (frameRef.current) cancelAnimationFrame(frameRef.current); };
  }, [target, decimals, prefix, suffix, duration]);

  return display;
}
