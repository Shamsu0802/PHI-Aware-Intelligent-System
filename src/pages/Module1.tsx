/* Module1.tsx
  */
import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { AlertTriangle, 
  Search, 
  Trash2, 
  ShieldAlert, 
  Brain, 
  BarChart3, 
  FileWarning  } from "lucide-react";

const API = "http://localhost:8000";
const sampleMessage =
  "Please send Rakesh Kumar's ECG report (MRN: 456789) to Dr. Anand at 9845012345. Patient DOB is 15/03/1978 and diagnosis includes Type-2 Diabetes.";

const severityClass = (s: string) => {
  const level = s?.toLowerCase();

  switch (level) {
    case "critical":
      return "bg-critical/15 text-critical border-critical/30";
    case "high":
      return "bg-accent/15 text-accent border-accent/30";
    case "medium":
      return "bg-warning/15 text-warning border-warning/30";
    default:
      return "bg-success/15 text-success border-success/30";
  }
};

const necessaryData = [
  {
    role: "Billing Staff",
    allowed: "Billing ID, Amount",
    detected: "Diagnosis, ECG Report",
    excess: "Diagnosis, ECG Report",
  },
  {
    role: "Lab Technician",
    allowed: "MRN, Test ID",
    detected: "MRN, DOB, Name",
    excess: "DOB, Name",
  },
  {
    role: "Referral Doctor",
    allowed: "Name, Diagnosis, MRN",
    detected: "Name, Diagnosis, MRN, Phone",
    excess: "Phone Number",
  },
];

export default function Module1() {
  const [message, setMessage] = useState("");
  const [analyzed, setAnalyzed] = useState(false);

  const [recipientType, setRecipientType] = useState("internal");
  const [time, setTime] = useState("day");
  const [attachment, setAttachment] = useState(false);

  const [phiEntities, setPhiEntities] = useState<any[]>([]);
  const [riskLevel, setRiskLevel] = useState("");
  const [riskScore, setRiskScore] = useState(0);
  const [confidence, setConfidence] = useState(0);
  const [explanation, setExplanation] = useState<any[]>([]);
  const [behaviorExplanation, setBehaviorExplanation] = useState<any>(null);

  /*
  Entity counts (security dashboard style)
  */
  const entityCounts = phiEntities.reduce((acc: any, e: any) => {
    acc[e.type] = (acc[e.type] || 0) + 1;
    return acc;
  }, {});

  const handleAnalyze = async () => {
    let text = message;

    if (!text.trim()) {
      text = sampleMessage;
      setMessage(sampleMessage);
    }

    try {
      const response = await fetch(`${API}/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          text,
          recipient_type: recipientType,
          time,
          attachment,
        }),
      });

      const result = await response.json();

      setPhiEntities(result.phi_entities || []);
      setRiskLevel(result.risk_level || "");
      setRiskScore(result.composite_risk_score || 0);
      setExplanation(Array.isArray(result.explanation) ? result.explanation : []);
      setBehaviorExplanation(result.behavior_explanation || null);

      setAnalyzed(true);
    } catch (error) {
      console.error("Analysis error:", error);
    }
  };

  /*
  Escape regex characters
  */
  const escapeRegex = (text: string) =>
    text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

  /*
  Highlight PHI inside message preview
  */
  const highlightMessage = () => {
    if (!message || phiEntities.length === 0) return message;

    let highlighted = message;

    phiEntities.forEach((entity) => {
      const value = entity.entity;
      if (!value) return;

      const color =
        entity.type === "PERSON"
          ? "bg-blue-200 dark:bg-blue-800"
          : entity.type === "PHONE"
          ? "bg-orange-200 dark:bg-orange-800"
          : entity.type === "MRN"
          ? "bg-red-200 dark:bg-red-800"
          : entity.type === "DISEASE"
          ? "bg-purple-200 dark:bg-purple-800"
          : entity.type === "POLICY_NUMBER"
          ? "bg-pink-200 dark:bg-pink-800"
          : "bg-yellow-200 dark:bg-yellow-800";

      const regex = new RegExp(escapeRegex(value), "gi");

      highlighted = highlighted.replace(
        regex,
        `<span class="${color} px-1 rounded">${value}</span>`
      );
    });

    return highlighted;
  };
// 🔥 FORMAT EXPLANATION DATA (CORRECT PLACE)

// 🔥 FORCE MAIN LINE FIRST
let mainLine = "";
const mainInsights: string[] = [];
const supporting: string[] = [];
const entities: string[] = [];

if (Array.isArray(explanation)) {
  explanation.forEach((exp) => {
    const text = String(exp);

    if (text.startsWith("The risk is primarily driven")) {
      mainLine = text;
    }

    else if (
      text.toLowerCase().includes("financial misuse") ||
      text.toLowerCase().includes("social engineering") ||
      text.toLowerCase().includes("unauthorized data access") ||
      text.toLowerCase().includes("re-identification") ||
      text.toLowerCase().includes("multiple sensitive identifiers")
    ) {
      mainInsights.push(text);
    }

    else if (text.includes("significantly contributed")) {
      entities.push(text);
    }

    else if (
      text.includes("Content sensitivity") ||
      text.includes("Contextual factors")
    ) {
      supporting.push(text);
    }
  });
}
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">
          Module 1 – PHI Leakage Intelligence Engine
        </h2>
        <p className="text-sm text-muted-foreground">
          Analyze healthcare communication messages for PHI exposure before
          sending
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">

        {/* INPUT PANEL */}

        <Card className="glass-card">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Message Input</CardTitle>
          </CardHeader>

          <CardContent className="space-y-3">

            <Textarea
              placeholder="Enter healthcare communication message to analyze PHI exposure..."
              className="min-h-[200px] resize-none bg-muted/50"
              value={message}
              onChange={(e) => {
                setMessage(e.target.value);
                setAnalyzed(false);
              }}
            />

            {analyzed && (
              <div className="p-3 rounded-md border text-sm bg-muted/30">
                <p className="text-xs text-muted-foreground mb-1">
                  PHI Highlight Preview
                </p>

                <div
                  dangerouslySetInnerHTML={{
                    __html: highlightMessage(),
                  }}
                />
              </div>
            )}

            {/* CONTROLS */}

            <div className="grid grid-cols-3 gap-3 text-sm">

              <div>
                <label className="text-xs text-muted-foreground">
                  Recipient Type
                </label>
                <select
                  value={recipientType}
                  onChange={(e) => setRecipientType(e.target.value)}
                  className="w-full border rounded p-2 bg-background"
                >
                  <option value="internal">Internal</option>
                  <option value="external">External</option>
                </select>
              </div>

              <div>
                <label className="text-xs text-muted-foreground">Time</label>
                <select
                  value={time}
                  onChange={(e) => setTime(e.target.value)}
                  className="w-full border rounded p-2 bg-background"
                >
                  <option value="day">Day</option>
                  <option value="late_night">Late Night</option>
                </select>
              </div>

              <div>
                <label className="text-xs text-muted-foreground">
                  Attachment
                </label>
                <select
                  value={attachment ? "yes" : "no"}
                  onChange={(e) => setAttachment(e.target.value === "yes")}
                  className="w-full border rounded p-2 bg-background"
                >
                  <option value="no">No</option>
                  <option value="yes">Yes</option>
                </select>
              </div>

            </div>

            <div className="flex gap-2">
              <Button onClick={handleAnalyze} className="gap-2">
                <Search className="h-4 w-4" /> Analyze Communication
              </Button>

              <Button
                variant="outline"
                onClick={() => {
                  setMessage("");
                  setAnalyzed(false);

                  // 🔥 FULL RESET
                  setPhiEntities([]);
                  setRiskLevel("");
                  setRiskScore(0);
                  setExplanation([]);
                  setBehaviorExplanation(null);
                }}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>

          </CardContent>
        </Card>


        {/* RESULTS */}

        <Card className="glass-card">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">
              Risk Analysis & PHI Intelligence Output
            </CardTitle>
          </CardHeader>

          <CardContent>

            {analyzed ? (
              <div className="space-y-4">

                {/* LEGEND */}

                <div className="flex flex-wrap gap-3 text-xs">
                  <span className="flex items-center gap-1">
                    <span className="w-3 h-3 rounded bg-blue-400"></span>
                    Name
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="w-3 h-3 rounded bg-orange-400"></span>
                    Phone
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="w-3 h-3 rounded bg-red-400"></span>
                    MRN
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="w-3 h-3 rounded bg-purple-400"></span>
                    Disease
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="w-3 h-3 rounded bg-yellow-400"></span>
                    Email
                  </span>

                  <span className="flex items-center gap-1">
                    <span className="w-3 h-3 rounded bg-green-400"></span>
                    Date
                  </span>

                  <span className="flex items-center gap-1">
                    <span className="w-3 h-3 rounded bg-gray-400"></span>
                    Record ID
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="w-3 h-3 rounded bg-pink-400"></span>
                    Financial
                  </span>                 
                </div>

                {/* ENTITY COUNTS */}

                <div className="text-xs text-muted-foreground">
                  {Object.keys(entityCounts).map((t) => (
                    <span key={t} className="mr-4">
                      {t}: <strong>{entityCounts[t]}</strong>
                    </span>
                  ))}
                </div>

                {/* PHI TAGS */}

                <div className="flex flex-wrap gap-2">
                  {phiEntities.map((p, index) => (
                    <Badge
                      key={index}
                      variant="outline"
                      className={`px-3 py-1 ${severityClass(riskLevel)}`}
                    >
                      {p.type}: {p.entity}
                    </Badge>
                  ))}
                </div>

                {/* RISK INFO */}

                <div className="rounded-lg bg-muted/50 p-4 space-y-2">
                  <p className="text-xs text-muted-foreground">
                    Risk Level
                  </p>
                  <p className="text-sm font-semibold">{riskLevel}</p>
                </div>

                {/* RISK GAUGE */}

                <div
  className={`rounded-lg border p-4 space-y-4 relative overflow-hidden ${
    riskLevel === "High"
      ? "border-l-4 border-l-red-500"
      : riskLevel === "Medium"
      ? "border-l-4 border-l-amber-500"
      : "border-l-4 border-l-green-500"
  }`}
>

                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium">
                      Composite Risk Score
                    </p>

                    <Badge
                      variant="outline"
                      className={severityClass(riskLevel)}
                    >
                      {riskLevel}
                    </Badge>
                  </div>

                  <div className="relative">
                    <Progress value={riskScore * 100} className="h-4" />

                    <span className="absolute inset-0 flex items-center justify-center text-[11px] font-mono font-bold">
                      {riskScore}
                    </span>
                  </div>

                  <div className="flex justify-between text-[10px] text-muted-foreground">
                    <span>Safe</span>
                    <span>Low</span>
                    <span>Medium</span>
                    <span>High</span>
                    <span>Critical</span>
                  </div>

                </div>

              </div>
            ) : (
              <div className="flex h-48 items-center justify-center text-sm text-muted-foreground">
                Enter a message and click Analyze to detect PHI entities
              </div>
            )}

          </CardContent>
        </Card>
      </div>
{/* 🔍 RISK EXPLANATION */}
{analyzed && (
<div className="rounded-lg border p-4 space-y-3">
      {riskLevel === "High" && (
    <div className="flex items-center gap-2 p-2 rounded-md animate-pulse">
      <AlertTriangle className="w-4 h-4 text-red-600" />
      <p className="text-[13px] font-semibold text-red-700 dark:text-red-300">
        High Risk Detected — Sensitive healthcare information exposure identified
      </p>
    </div>
  )}
  
  <p className="text-sm font-bold text-primary">
    Why this risk?
  </p>
  
  
  
  <div className="space-y-4">

  {/* 🔵 MAIN INSIGHT */}
  {mainLine && (
    <div className="flex items-start gap-2 bg-blue-50 dark:bg-blue-900/20 p-3 rounded-md border-l-4 border-blue-500">
      <ShieldAlert className="w-4 h-4 text-blue-600 mt-0.5" />
      <p className="text-[14px] font-bold text-blue-700 dark:text-blue-300 leading-relaxed">
        {mainLine}
      </p>
    </div>
  )}

  {/* 🔴 RISK IMPLICATIONS */}
  {mainInsights.length > 0 && (
    <div className="bg-red-50 dark:bg-red-900/20 p-3 rounded-md border border-red-200 dark:border-red-800 space-y-2">
      
      <div className="flex items-center gap-2">
        <AlertTriangle className="w-4 h-4 text-red-600" />
        <p className="text-[13px] font-semibold text-red-700 dark:text-red-300">
          Risk Implications
        </p>
      </div>

      {mainInsights.map((text, i) => (
        <p key={i} className="text-[13px] text-muted-foreground pl-5">
          • {text}
        </p>
      ))}

    </div>
  )}

  {/* 🟡 CONTRIBUTION */}
  {supporting.length > 0 && (
    <div className="bg-amber-50 dark:bg-amber-900/20 p-3 rounded-md border border-amber-200 dark:border-amber-800 space-y-2">

      <div className="flex items-center gap-2">
        <BarChart3 className="w-4 h-4 text-amber-600" />
        <p className="text-[13px] font-semibold text-amber-700 dark:text-amber-300">
          Risk Contribution
        </p>
      </div>

      {supporting.map((text, i) => (
        <p key={i} className="text-[13px] text-muted-foreground pl-5">
          • {text}
        </p>
      ))}

    </div>
  )}

  {/* 🔷 ENTITY PROOF */}
  {entities.length > 0 && (
    <div className="bg-indigo-50 dark:bg-indigo-900/20 p-3 rounded-md border border-indigo-200 dark:border-indigo-800 space-y-2">

      <div className="flex items-center gap-2">
        <FileWarning className="w-4 h-4 text-indigo-600" />
        <p className="text-[13px] font-semibold text-indigo-700 dark:text-indigo-300">
          Key Risk Contributors
        </p>
      </div>

      {entities.map((text, i) => (
        <p key={i} className="text-[13px] text-foreground pl-5 font-medium">
          • {text}
        </p>
      ))}

    </div>
  )}
  {/* 🔷 FINAL SCORE */}
<div className="bg-gray-50 dark:bg-gray-900/30 p-3 rounded-md border space-y-1">

  <div className="flex items-center gap-2">
    <BarChart3 className="w-4 h-4 text-gray-600" />
    <p className="text-[13px] font-semibold text-gray-700 dark:text-gray-300">
      Final Risk Score
    </p>
  </div>

  <p className="text-[13px] text-muted-foreground pl-5">
    Composite risk score computed as{" "}
    <span className={`font-mono font-bold ${
    riskLevel === "High"
      ? "text-red-600"
      : riskLevel === "Medium"
      ? "text-amber-600"
      : "text-green-600"
  }`}>
      {riskScore.toFixed(3)}
    </span>
  </p>

</div>

{/* 🔥 ADD THIS NEW BLOCK BELOW */}

<div className="rounded-lg border p-4 space-y-2 bg-muted/30">

  <div className="flex items-center gap-2">
    <Brain className="w-4 h-4 text-primary" />
    <p className="text-sm font-bold text-primary">
      Behavior Insight
    </p>
  </div>

  <p className="text-[13px] text-muted-foreground pl-6">
    {behaviorExplanation ? (
      behaviorExplanation.percentage > 0 ? (
        <>Behavioral contribution: {behaviorExplanation.percentage}%</>
      ) : (
        <>No significant behavioral anomaly detected</>
      )
    ) : (
      <>No behavioral data available</>
    )}
  </p>

</div>


</div>

</div>
)}


      

    </div>
  );
}