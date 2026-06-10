import type { DocBlock } from "@/content/docs";

/** Renders an article's content blocks. Dependency-free (no MDX). */
export function DocBody({ blocks }: { blocks: DocBlock[] }) {
  return (
    <div className="prose">
      {blocks.map((block, i) => {
        switch (block.type) {
          case "h":
            return <h2 key={i}>{block.text}</h2>;
          case "p":
            return <p key={i}>{block.text}</p>;
          case "ul":
            return (
              <ul key={i}>
                {block.items.map((item, j) => (
                  <li key={j}>{item}</li>
                ))}
              </ul>
            );
          case "ol":
            return (
              <ol key={i} className="prose-ol">
                {block.items.map((item, j) => (
                  <li key={j}>{item}</li>
                ))}
              </ol>
            );
          case "code":
            return (
              <pre key={i} className="doc-code">
                <code>{block.code}</code>
              </pre>
            );
          case "callout":
            return (
              <p key={i} className="doc-callout">
                {block.text}
              </p>
            );
          default:
            return null;
        }
      })}
    </div>
  );
}
