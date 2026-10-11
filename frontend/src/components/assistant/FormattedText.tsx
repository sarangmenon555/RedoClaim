"use client";

export default function FormattedText({ text }: { text: string }) {
  const blocks: { type: "p" | "ul"; lines: string[] }[] = [];
  for (const raw of text.split("\n")) {
    const line = raw.trim();
    if (!line) {
      continue;
    }
    const isItem = /^[-*]\s+/.test(line);
    const clean = line.replace(/^[-*]\s+/, "").replace(/\*\*(.+?)\*\*/g, "$1").replace(/^#+\s*/, "");
    const last = blocks[blocks.length - 1];
    if (isItem) {
      if (last && last.type === "ul") last.lines.push(clean);
      else blocks.push({ type: "ul", lines: [clean] });
    } else {
      blocks.push({ type: "p", lines: [clean] });
    }
  }
  return (
    <div className="space-y-3 text-sm leading-relaxed" style={{ color: "var(--text-primary)" }}>
      {blocks.map((block, i) =>
        block.type === "p" ? (
          <p key={i}>{block.lines[0]}</p>
        ) : (
          <ul key={i} className="space-y-1.5 pl-4 list-disc" style={{ color: "var(--text-secondary)" }}>
            {block.lines.map((l, j) => (
              <li key={j}>{l}</li>
            ))}
          </ul>
        )
      )}
    </div>
  );
}
