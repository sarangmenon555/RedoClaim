"use client";
import React from "react";

type Block =
  | { type: "p"; text: string }
  | { type: "h"; text: string }
  | { type: "ul" | "ol"; items: string[] }
  | { type: "table"; header: string[]; rows: string[][] };

const INLINE = /(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\([^)\s]+\)|https?:\/\/[^\s)<]+|[\w.+-]+@[\w-]+\.[\w.-]+)/g;

function safeHref(url: string): string | null {
  if (/^(https?:|mailto:|tel:)/i.test(url)) return url;
  return null;
}

function inline(text: string, keyBase: string): React.ReactNode[] {
  const nodes: React.ReactNode[] = [];
  let last = 0;
  let index = 0;
  for (const match of text.matchAll(INLINE)) {
    const token = match[0];
    const start = match.index ?? 0;
    if (start > last) nodes.push(text.slice(last, start));
    const key = `${keyBase}-${index++}`;
    const linkStyle = { color: "#A78BFA", textDecoration: "underline", wordBreak: "break-word" as const };
    if (token.startsWith("**")) {
      nodes.push(<strong key={key}>{token.slice(2, -2)}</strong>);
    } else if (token.startsWith("`")) {
      nodes.push(
        <code key={key} className="px-1 rounded text-xs" style={{ background: "var(--surface-2)" }}>
          {token.slice(1, -1)}
        </code>
      );
    } else if (token.startsWith("[")) {
      const split = token.indexOf("](");
      const label = token.slice(1, split);
      const href = safeHref(token.slice(split + 2, -1));
      nodes.push(
        href ? (
          <a key={key} href={href} target="_blank" rel="noopener noreferrer" style={linkStyle}>{label}</a>
        ) : (
          label
        )
      );
    } else if (/^https?:/i.test(token)) {
      const trimmed = token.replace(/[.,;:]+$/, "");
      nodes.push(
        <a key={key} href={trimmed} target="_blank" rel="noopener noreferrer" style={linkStyle}>{trimmed}</a>
      );
      if (trimmed.length < token.length) nodes.push(token.slice(trimmed.length));
    } else {
      nodes.push(<a key={key} href={`mailto:${token}`} style={linkStyle}>{token}</a>);
    }
    last = start + token.length;
  }
  if (last < text.length) nodes.push(text.slice(last));
  return nodes;
}

const splitRow = (line: string) =>
  line.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map((c) => c.trim());

const isSeparator = (line: string) => /^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$/.test(line);

function parse(text: string): Block[] {
  const lines = text.replace(/\r/g, "").split("\n");
  const blocks: Block[] = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i].trim();
    if (!line) {
      i++;
      continue;
    }
    if (line.startsWith("|")) {
      const rows: string[][] = [];
      let header: string[] | null = null;
      while (i < lines.length && lines[i].trim().startsWith("|")) {
        const current = lines[i].trim();
        if (isSeparator(current)) {
          if (!header && rows.length === 1) header = rows.shift() || null;
        } else {
          rows.push(splitRow(current));
        }
        i++;
      }
      blocks.push({ type: "table", header: header || [], rows });
      continue;
    }
    const heading = line.match(/^#{1,4}\s+(.*)$/);
    if (heading) {
      blocks.push({ type: "h", text: heading[1] });
      i++;
      continue;
    }
    if (/^[-*\u2022]\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\s*[-*\u2022]\s+/.test(lines[i])) {
        items.push(lines[i].trim().replace(/^[-*\u2022]\s+/, ""));
        i++;
      }
      blocks.push({ type: "ul", items });
      continue;
    }
    if (/^\d+[.)]\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\s*\d+[.)]\s+/.test(lines[i])) {
        items.push(lines[i].trim().replace(/^\d+[.)]\s+/, ""));
        i++;
      }
      blocks.push({ type: "ol", items });
      continue;
    }
    blocks.push({ type: "p", text: line });
    i++;
  }
  return blocks;
}

export default function FormattedText({ text }: { text: string }) {
  const blocks = parse(text);
  return (
    <div className="space-y-3 text-sm leading-relaxed" style={{ color: "var(--text-primary)" }}>
      {blocks.map((block, i) => {
        if (block.type === "h") {
          return (
            <p key={i} className="font-semibold pt-1">
              {inline(block.text, `h${i}`)}
            </p>
          );
        }
        if (block.type === "p") {
          return <p key={i}>{inline(block.text, `p${i}`)}</p>;
        }
        if (block.type === "ul" || block.type === "ol") {
          const Tag = block.type === "ul" ? "ul" : "ol";
          return (
            <Tag
              key={i}
              className={`space-y-1.5 pl-5 ${block.type === "ul" ? "list-disc" : "list-decimal"}`}
              style={{ color: "var(--text-secondary)" }}
            >
              {block.items.map((item, j) => (
                <li key={j}>{inline(item, `l${i}-${j}`)}</li>
              ))}
            </Tag>
          );
        }
        if (block.type !== "table") return null;
        return (
          <div key={i} className="overflow-x-auto rounded-lg" style={{ border: "1px solid var(--surface-4)" }}>
            <table className="w-full text-xs">
              {block.header.length > 0 && (
                <thead style={{ background: "var(--surface-2)" }}>
                  <tr>
                    {block.header.map((cell, j) => (
                      <th key={j} className="text-left font-semibold px-3 py-2" style={{ color: "var(--text-primary)" }}>
                        {inline(cell, `th${i}-${j}`)}
                      </th>
                    ))}
                  </tr>
                </thead>
              )}
              <tbody>
                {block.rows.map((row, r) => (
                  <tr key={r} style={{ borderTop: "1px solid var(--surface-4)" }}>
                    {row.map((cell, c) => (
                      <td
                        key={c}
                        className={`px-3 py-2 align-top ${c === 0 ? "font-medium whitespace-nowrap" : ""}`}
                        style={{ color: c === 0 ? "var(--text-primary)" : "var(--text-secondary)" }}
                      >
                        {inline(cell, `td${i}-${r}-${c}`)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
      })}
    </div>
  );
}
