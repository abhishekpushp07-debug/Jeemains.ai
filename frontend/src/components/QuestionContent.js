import React, { useMemo } from "react";
import katex from "katex";
import "katex/dist/katex.min.css";
import { SourceImage } from "./Shared";
export function MathText({ text = "" }) {
  const parts = useMemo(
    () => String(text).split(/(\$\$[\s\S]+?\$\$|\$[^$\n]+?\$)/g),
    [text],
  );
  return (
    <div className="math-text">
      {parts.map((p, i) =>
        p.startsWith("$") ? (
          <span
            key={i}
            dangerouslySetInnerHTML={{
              __html: katex.renderToString(p.replace(/^\$\$?|\$\$?$/g, ""), {
                throwOnError: false,
                displayMode: p.startsWith("$$"),
                trust: false,
                output: "htmlAndMathml",
              }),
            }}
          />
        ) : (
          <React.Fragment key={i}>{p}</React.Fragment>
        ),
      )}
    </div>
  );
}
export function QuestionContent({
  question: q,
  base,
  solution = false,
  onAssetError,
  onAssetLoad,
  gradeVersion = "original",
  readable = false,
}) {
  const count = solution
    ? (q.solution_asset_count ?? q.s_refs?.length)
    : (q.asset_count ?? q.q_refs?.length);
  const refs = solution ? q.s_refs : q.q_refs;
  const text = solution ? q.solution : q.text;
  const alt = solution ? q.solution_accessible_text : q.accessible_text;
  if (q.render_mode === "source" && count)
    return (
      <div className="question-source">
        {Array.from({ length: count }, (_, i) => (
          <SourceImage
            key={base + i}
            readable={readable && !solution}
            testId={'source-' + q.id + '-' + (solution ? 'solution' : 'question') + '-' + i}
            path={`${base}/asset/${solution ? "solution" : "question"}/${i}${gradeVersion !== "original" ? "?score_version=" + encodeURIComponent(gradeVersion) : ""}`}
            alt={
              alt ||
              "Unreviewed source region; accessible description pending reviewer approval"
            }
            onError={() => onAssetError?.(i)}
            onLoad={() => onAssetLoad?.(i)}
          />
        ))}
        {alt && (
          <details>
            <summary data-testid="accessible-source-text">
              Read accessible text
            </summary>
            <MathText text={alt} />
          </details>
        )}
        {refs && (
          <small className="source-reference">
            Source {solution ? "solution" : "question"} pages:{" "}
            {refs.map((r) => r.page).join(", ")}
          </small>
        )}
      </div>
    );
  return <MathText text={text} />;
}
