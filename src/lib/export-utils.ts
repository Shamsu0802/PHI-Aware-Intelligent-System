import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";

export function downloadCSV(filename: string, headers: string[], rows: string[][]) {
  const escape = (v: string) => `"${v.replace(/"/g, '""')}"`;
  const lines = [headers.map(escape).join(","), ...rows.map((r) => r.map(escape).join(","))];
  const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8;" });
  triggerDownload(blob, `${filename}.csv`);
}

export function downloadPDF(
  filename: string,
  title: string,
  headers: string[],
  rows: string[][],
  subtitle?: string
) {
  const doc = new jsPDF({ orientation: rows[0]?.length > 5 ? "landscape" : "portrait" });

  doc.setFontSize(16);
  doc.text(title, 14, 18);

  if (subtitle) {
    doc.setFontSize(9);
    doc.setTextColor(120);
    doc.text(subtitle, 14, 25);
    doc.setTextColor(0);
  }

  autoTable(doc, {
    head: [headers],
    body: rows,
    startY: subtitle ? 30 : 24,
    styles: { fontSize: 8, cellPadding: 3 },
    headStyles: { fillColor: [111, 168, 220], textColor: 255, fontStyle: "bold" },
    alternateRowStyles: { fillColor: [247, 249, 252] },
  });

  doc.save(`${filename}.pdf`);
}

function triggerDownload(blob: Blob, name: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
