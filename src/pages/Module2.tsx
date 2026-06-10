import { useState, useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Upload } from "lucide-react";

const API = "http://localhost:8000";

/* hospital domains for internal detection */
const HOSPITAL_DOMAINS = [
  "hospital.com",
  "hospital.org",
  "medcenter.org",
  "healthcare.net",
  "clinic.local"
];

export default function Module2() {

  const [recipient, setRecipient] = useState("");
  const [subject, setSubject] = useState("");
  const [message, setMessage] = useState("");

  const [recipientType, setRecipientType] = useState("external");

  const [analyzed, setAnalyzed] = useState(false);

  const [riskScore, setRiskScore] = useState(0);
  const [riskLevel, setRiskLevel] = useState("Low");
  const [decision, setDecision] = useState("");

  const [rewriteSuggestion, setRewriteSuggestion] = useState("");

  const [sending, setSending] = useState(false);
  const [attachment, setAttachment] = useState(false);

  const debounceRef = useRef<any>(null);

  /* animation state */
  const [riskPulse, setRiskPulse] = useState(false);


  /* ---------------- RECIPIENT DOMAIN DETECTION ---------------- */

  useEffect(() => {

    if (!recipient.includes("@")) return;

    const domain = recipient.split("@")[1].toLowerCase();

    if (HOSPITAL_DOMAINS.includes(domain)) {
      setRecipientType("internal");
    } else {
      setRecipientType("external");
    }

  }, [recipient]);


  /* ---------------- REAL TIME ANALYSIS ---------------- */

  useEffect(() => {

    if (!message || message.trim().length < 3) {
      setAnalyzed(false);
      setRewriteSuggestion("");
      return;
    }

    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    debounceRef.current = setTimeout(() => {
      analyzeMessage();
    }, 500);

  }, [message, recipient, attachment]);


  /* ---------------- RISK ANIMATION ---------------- */

  useEffect(() => {

    if (!riskLevel) return;

    setRiskPulse(true);

    const timer = setTimeout(() => {
      setRiskPulse(false);
    }, 500);

    return () => clearTimeout(timer);

  }, [riskLevel]);


  const analyzeMessage = async () => {

    try {

      const response = await fetch(`${API}/secure-communication/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          text: message,
          recipient_type: recipientType,
          time: "day",
          attachment: attachment
        })
      });

      const result = await response.json();

      const risk = result?.risk_analysis;

      const score = risk?.risk_score ?? 0;

      setRiskScore(score);
      setRiskLevel(risk?.risk_level ?? "Low");
      setDecision(risk?.decision ?? "ALLOW");

      setRewriteSuggestion(result?.rewrite_suggestion ?? "");

      setAnalyzed(true);

    } catch (err) {

      console.error("Secure communication analysis failed:", err);

    }

  };


  /* ---------------- ACCEPT SAFE REWRITE ---------------- */

  const acceptRewrite = () => {

    if (!rewriteSuggestion) return;

    setMessage(rewriteSuggestion);

  };


  /* ---------------- SEND EMAIL ---------------- */

  const handleSendEmail = async () => {

    try {

      setSending(true);

      const safeMessage = rewriteSuggestion || message;

      const response = await fetch(`${API}/secure-communication/send`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          recipient: recipient,
          message: safeMessage
        })
      });

      const result = await response.json();

      if (result.status === "sent") {
        alert("Secure message sent successfully");
      } else {
        alert("Message sending failed");
      }

    } catch (error) {

      console.error("Email send error:", error);
      alert("Failed to send email");

    } finally {

      setSending(false);

    }

  };


  /* ---------------- RISK BANNER ---------------- */

  const riskBanner = () => {

    if (!analyzed) return null;

    if (riskLevel === "Low") {
      return (
        <div className="p-3 rounded-md bg-green-50 border border-green-200 text-green-700 text-sm">
          Low risk. No critical exploit combinations detected.
        </div>
      );
    }

    if (riskLevel === "Medium") {
      return (
        <div className="p-3 rounded-md bg-yellow-50 border border-yellow-200 text-orange-700 text-sm">
          Moderate risk. Identifiers detected in message.
        </div>
      );
    }

    return (
      <div className="p-3 rounded-md bg-red-50 border border-red-200 text-red-700 text-sm">
        High exploitability detected. Insurance identifiers + diagnosis present in external message.
      </div>
    );

  };


  const sendDisabled =
    recipientType === "external" && riskLevel === "High";


  return (
    <div className="space-y-6">

      <div className="flex items-start justify-between">

  <div>
    <h2 className="text-2xl font-bold">
      Module 2 – Secure Communication Filtering
    </h2>

    <p className="text-sm text-muted-foreground">
      Simulate secure message sending with PHI protection and channel risk analysis
    </p>
  </div>

  <div className="flex items-center gap-2 text-xs text-muted-foreground mt-1">

    <span className="relative flex h-2 w-2">
      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
      <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
    </span>

    <span>Live PHI Monitoring</span>

  </div>

</div>


      {/* RECIPIENT TYPE INDICATOR */}

      <div className="flex gap-3 items-center">

        {recipientType === "internal" ? (
          <Badge className="bg-green-100 text-green-700 border-green-300">
            🟢 Internal Communication
          </Badge>
        ) : (
          <Badge className="bg-blue-100 text-blue-700 border-blue-300">
            🔵 External Communication
          </Badge>
        )}

        {analyzed && (
          <Badge
            className={`transition-all duration-300 ${
              riskPulse ? "scale-110 shadow-lg" : "scale-100"
            } ${
              riskLevel === "High"
                ? "bg-red-100 text-red-700"
                : riskLevel === "Medium"
                ? "bg-yellow-100 text-yellow-700"
                : "bg-green-100 text-green-700"
            }`}
          >
            {riskLevel.toUpperCase()}
          </Badge>
        )}

      </div>


      {/* Risk score bar */}

      {analyzed && (
        <div className="w-full bg-muted rounded h-2">
          <div
            className={`h-2 rounded transition-all duration-500 ${
              riskLevel === "High"
                ? "bg-red-500"
                : riskLevel === "Medium"
                ? "bg-yellow-500"
                : "bg-green-500"
            }`}
            style={{ width: `${Math.min(riskScore * 100, 100)}%` }}
          />
        </div>
      )}


      {riskBanner()}


      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">

        {/* Message Composer */}

        <Card className="glass-card">

          <CardHeader className="pb-2">
            <CardTitle className="text-base">
              Message Composer
            </CardTitle>
          </CardHeader>

          <CardContent className="space-y-3">

            <div>
              <Label className="text-xs">Recipient</Label>
              <Input
                placeholder="recipient@email.com"
                className="bg-muted/50"
                value={recipient}
                onChange={(e) => setRecipient(e.target.value)}
              />
            </div>

            <div>
              <Label className="text-xs">Subject</Label>
              <Input
                placeholder="Patient Report Sharing"
                className="bg-muted/50"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
              />
            </div>

            <div>
              <Label className="text-xs">Message Content</Label>

              <Textarea
                className="min-h-[120px] bg-muted/50"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
              />

            </div>

            {/* ATTACHMENT */}

            <div className="rounded-lg border-2 border-dashed border-border p-6 text-center">

              <Upload className="mx-auto h-6 w-6 text-muted-foreground mb-2" />

              <label className="text-xs text-muted-foreground cursor-pointer">

                <input
                  type="checkbox"
                  className="mr-2"
                  onChange={(e) => setAttachment(e.target.checked)}
                />

                Attach File

              </label>

            </div>

            <Button
              className="w-full"
              onClick={handleSendEmail}
              disabled={sendDisabled || sending}
            >
              {sendDisabled
                ? "🔒 Accept Safe Rewrite to Enable Sending"
                : "Send Securely"}
            </Button>

          </CardContent>

        </Card>


        {/* Channel Risk */}

        <Card className="glass-card">

          <CardHeader className="pb-2">
            <CardTitle className="text-base">
              Channel Risk Analysis
            </CardTitle>
          </CardHeader>

          <CardContent>

            {analyzed ? (

              <div className="space-y-2 text-sm">

                <div className="flex justify-between">
                  <span className="text-muted-foreground">Recipient</span>
                  <span className="font-mono">{recipient}</span>
                </div>

                <div className="flex justify-between">
                  <span className="text-muted-foreground">Channel Type</span>
                  <span>Email</span>
                </div>

                <div className="flex justify-between">
                  <span className="text-muted-foreground">Decision</span>

                  <Badge
                    variant="outline"
                    className={
                      decision === "BLOCK"
                        ? "bg-red-100 text-red-700 border-red-300"
                        : "bg-green-100 text-green-700 border-green-300"
                    }
                  >
                    {decision}
                  </Badge>

                </div>

              </div>

            ) : (

              <p className="text-sm text-muted-foreground text-center py-4">
                Type or paste message to analyze risk
              </p>

            )}

          </CardContent>

        </Card>

      </div>


      {/* SAFE REWRITE PANEL */}

      {rewriteSuggestion && (

        <Card className="glass-card">

          <CardHeader>
            <CardTitle className="text-base">
              🔐 Suggested Safe Version
            </CardTitle>
          </CardHeader>

          <CardContent>

            <div className="bg-muted p-3 rounded-md font-mono text-sm">
              {rewriteSuggestion}
            </div>

            <div className="flex gap-3 mt-3">

              <Button onClick={acceptRewrite}>
                Accept Rewrite
              </Button>

              <Button variant="outline">
                Edit Manually
              </Button>

            </div>

          </CardContent>

        </Card>

      )}

    </div>
  );
}