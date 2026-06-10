import { useCallback, useRef } from "react";

// Generate a short alert beep using Web Audio API (no file needed)
function playAlertTone() {
  try {
    const ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.type = "sine";
    osc.frequency.setValueAtTime(880, ctx.currentTime); // A5
    osc.frequency.setValueAtTime(660, ctx.currentTime + 0.1); // E5

    gain.gain.setValueAtTime(0.15, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.4);

    osc.start(ctx.currentTime);
    osc.stop(ctx.currentTime + 0.4);

    // Cleanup
    setTimeout(() => ctx.close(), 500);
  } catch {
    // Audio not supported – silent fallback
  }
}

function sendBrowserNotification(title: string, body: string) {
  if (!("Notification" in window) || Notification.permission !== "granted") return;

  try {
    new Notification(title, {
      body,
      icon: "/favicon.ico",
      tag: "phi-alert", // collapse repeated notifications
    });
  } catch {
    // Notification API not available
  }
}

export function useAlertNotification() {
  const lastSoundRef = useRef(0);

  const requestPermission = useCallback(async () => {
    if ("Notification" in window && Notification.permission === "default") {
      await Notification.requestPermission();
    }
  }, []);

  const notify = useCallback((title: string, risk: string) => {
    if (risk !== "Critical" && risk !== "High") return;

    // Throttle sound to once per 3 seconds
    const now = Date.now();
    if (now - lastSoundRef.current > 3000) {
      playAlertTone();
      lastSoundRef.current = now;
    }

    if (risk === "Critical") {
      sendBrowserNotification("⚠️ Critical PHI Alert", title);
    }
  }, []);

  return { notify, requestPermission };
}
