import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  ShieldAlert,
  Video,
  VideoOff,
  ShieldCheck,
  ShieldOff
} from "lucide-react";

const API = "http://127.0.0.1:8000";

export default function Module3() {

  const [guardActive, setGuardActive] = useState(false);
  const [privacyBlocked, setPrivacyBlocked] = useState(false);
  const [reason, setReason] = useState("AUTHORIZED");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const [userName, setUserName] = useState("");
  const [confidence, setConfidence] = useState<number | null>(null);

  const [streamKey, setStreamKey] = useState(Date.now());

  /* ======================================================
     AUTO START / STOP SCREEN GUARD
  ====================================================== */

  useEffect(() => {

    const startGuard = async () => {
      try {
        await fetch(`${API}/screen/start`);
        setGuardActive(true);
        setStreamKey(Date.now());
      } catch (err) {
        console.error("Failed to auto start guard", err);
      }
    };

    startGuard();

    return () => {
      fetch(`${API}/screen/stop`);
    };

  }, []);

  /* ======================================================
     POLL BACKEND PRIVACY STATUS
  ====================================================== */

  useEffect(() => {

    const pollPrivacy = async () => {

      try {

        const res = await fetch(`${API}/screen/status`);
        const data = await res.json();

        setPrivacyBlocked(data.privacy_state === "BLOCK");
        setReason(data.reason || "AUTHORIZED");

        if (data.name) setUserName(data.name);
        if (data.confidence) setConfidence(data.confidence);

      } catch (err) {

        console.error("Privacy polling failed", err);

      }

    };

    pollPrivacy();

    const interval = setInterval(pollPrivacy, 1000);

    return () => clearInterval(interval);

  }, []);

  /* ======================================================
     START / STOP CONTROLS
  ====================================================== */

  const startGuard = async () => {

    try {

      setLoading(true);

      await fetch(`${API}/screen/start`);
      setGuardActive(true);

      setStreamKey(Date.now());

    } catch (err) {

      console.error("Failed to start screen guard:", err);

    } finally {

      setLoading(false);

    }

  };

  const stopGuard = async () => {

    try {

      setLoading(true);

      await fetch(`${API}/screen/stop`);
      setGuardActive(false);

    } catch (err) {

      console.error("Failed to stop screen guard:", err);

    } finally {

      setLoading(false);

    }

  };

  /* ======================================================
     STATUS BADGE
  ====================================================== */

  const renderStatusBadge = () => {

    if (!privacyBlocked) {
      return (
        <Badge className="bg-green-100 text-green-700 border-green-300">
          SAFE
        </Badge>
      );
    }

    return (
      <Badge className="bg-red-100 text-red-700 border-red-300">
        BLOCKED
      </Badge>
    );

  };

  /* ======================================================
     REASON TEXT
  ====================================================== */

  const renderReason = () => {

    const map: any = {
      CAMERA_COVERED: "Camera covered / hand near lens",
      PHONE_DETECTED: "Mobile phone detected",
      MULTIPLE_FACES: "Multiple viewers detected",
      UNAUTHORIZED_USER: "Unauthorized viewer",
      AUTHORIZED: "Authorized user"
    };

    return map[reason] || "Monitoring";

  };

  return (
    <div className="space-y-6">

      {/* HEADER */}

      <div className="flex items-start justify-between">

        <div>
          <h2 className="text-2xl font-bold">
            Module 3 – Real-Time Screen Privacy Guard
          </h2>

          <p className="text-sm text-muted-foreground">
            Webcam-based monitoring to prevent shoulder surfing, phone recording,
            and unauthorized screen viewing
          </p>
        </div>

        <div className="flex items-center gap-2 text-sm font-medium text-green-600">

          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
          </span>

          Live Privacy Monitoring

        </div>

      </div>

      {/* PRIVACY BANNER */}

      <div
        className={`flex items-center gap-3 p-4 rounded-lg ${
          !privacyBlocked
            ? "bg-green-100 text-green-800"
            : "bg-red-100 text-red-800"
        }`}
      >

        {!privacyBlocked ? (
          <ShieldCheck className="w-6 h-6" />
        ) : (
          <ShieldOff className="w-6 h-6" />
        )}

        <span className="font-medium">

          {reason === "AUTHORIZED" && "Authorized user detected"}
          {reason === "UNAUTHORIZED_USER" && "🚫 Unauthorized viewer detected"}
          {reason === "MULTIPLE_FACES" && "👥 Multiple people detected"}
          {reason === "PHONE_DETECTED" && "📱 Mobile phone detected"}
          {reason === "CAMERA_COVERED" && "📷 Camera covered or tampered"}

        </span>

      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">

        {/* SECURE ACTIVITY PANEL */}

        <Card className="glass-card lg:col-span-2">

          <CardHeader className="pb-2">

            <div className="flex items-center justify-between">

              <CardTitle className="text-base">
                Secure Activity Panel
              </CardTitle>

              <Button
                size="sm"
                variant={guardActive ? "destructive" : "default"}
                onClick={guardActive ? stopGuard : startGuard}
                disabled={loading}
                className="gap-2"
              >

                {guardActive ? (
                  <>
                    <VideoOff className="h-3.5 w-3.5" />
                    Stop Guard
                  </>
                ) : (
                  <>
                    <Video className="h-3.5 w-3.5" />
                    Start Guard
                  </>
                )}

              </Button>

            </div>

          </CardHeader>

          <CardContent>

            <div className="relative">

              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                disabled={privacyBlocked}
                className={`w-full min-h-[220px] rounded-md border p-3 text-sm ${
                  privacyBlocked
                    ? "blur-md select-none cursor-not-allowed"
                    : ""
                }`}
                placeholder={
                  privacyBlocked
                    ? "🔒 Screen blocked due to privacy risk"
                    : "Paste healthcare message or perform activity..."
                }
              />

            </div>

          </CardContent>

        </Card>

        {/* RIGHT PANEL */}

        <div className="space-y-4">

          {/* STATUS PANEL */}

          <Card className="glass-card">

            <CardHeader className="pb-2">

              <CardTitle className="text-base flex items-center gap-2">
                <ShieldAlert className="h-4 w-4 text-warning" />
                Privacy Status
              </CardTitle>

            </CardHeader>

            <CardContent className="space-y-3">

              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Guard Status</span>
                {renderStatusBadge()}
              </div>

              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Detection Reason</span>
                <span className="font-medium text-right">{renderReason()}</span>
              </div>

              {userName && !privacyBlocked && (
                <>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Authorized User</span>
                    <span className="font-medium">{userName}</span>
                  </div>

                  {confidence !== null && (
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Confidence</span>
                      <span className="font-medium">{confidence.toFixed(1)}%</span>
                    </div>
                  )}
                </>
              )}

            </CardContent>

          </Card>

          {/* LIVE CAMERA MONITOR */}

          <Card className="glass-card">

            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-center">
                Live Privacy Monitor
              </CardTitle>
            </CardHeader>

            <CardContent>

              <div
                className={`rounded-lg overflow-hidden border-2 ${
                  privacyBlocked ? "border-red-500" : "border-green-500"
                }`}
              >

                <img
                  key={streamKey}
                  src={`${API}/screen/stream?t=${streamKey}`}
                  alt="Live Camera"
                  className="w-full object-cover"
                />

              </div>

              <p className="text-xs text-center mt-2 text-muted-foreground">
                Real-time visual privacy protection
              </p>

            </CardContent>

          </Card>

        </div>

      </div>

    </div>
  );

}