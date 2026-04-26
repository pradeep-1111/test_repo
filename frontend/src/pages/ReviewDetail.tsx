import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getReview } from "../api/reviews";
import type { ReviewDetail as ReviewDetailType } from "../types/review";

function severityClass(severity: string) {
  if (severity === "critical") return "bg-red-100 text-red-800";
  if (severity === "high") return "bg-orange-100 text-orange-800";
  if (severity === "medium") return "bg-yellow-100 text-yellow-800";
  return "bg-slate-100 text-slate-700";
}

export function ReviewDetail() {
  const { reviewId } = useParams();
  const [review, setReview] = useState<ReviewDetailType | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!reviewId) return;

    getReview(reviewId)
      .then(setReview)
      .finally(() => setLoading(false));
  }, [reviewId]);

  if (loading) return <p>Loading review...</p>;
  if (!review) return <p>Review not found.</p>;

  return (
    <div className="space-y-6">
      <Link to="/" className="text-sm text-blue-600 hover:underline">
        ← Back to dashboard
      </Link>

      <section>
        <h1 className="text-3xl font-bold">
          {review.repo_full_name} PR #{review.pr_number}
        </h1>
        <p className="mt-2 text-slate-600">
          Conclusion: <strong>{review.conclusion}</strong>
        </p>
      </section>

      <section className="rounded-2xl bg-white p-5 shadow-sm">
        <h2 className="mb-3 font-semibold">Summary</h2>
        <pre className="whitespace-pre-wrap text-sm text-slate-700">
          {review.summary_markdown}
        </pre>
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-semibold">
          Findings ({review.findings.length})
        </h2>

        {review.findings.length === 0 ? (
          <div className="rounded-2xl bg-white p-5 shadow-sm">
            No findings.
          </div>
        ) : (
          review.findings.map((finding, index) => (
            <article key={index} className="rounded-2xl bg-white p-5 shadow-sm">
              <div className="flex flex-wrap items-center gap-2">
                <span
                  className={`rounded-full px-2 py-1 text-xs font-medium ${severityClass(
                    finding.severity
                  )}`}
                >
                  {finding.severity}
                </span>
                <span className="rounded-full bg-blue-100 px-2 py-1 text-xs text-blue-800">
                  {finding.category}
                </span>
                <span className="text-xs text-slate-500">
                  {finding.source}
                </span>
              </div>

              <h3 className="mt-3 text-lg font-semibold">{finding.title}</h3>

              <p className="mt-2 text-sm text-slate-700">
                {finding.explanation}
              </p>

              <p className="mt-3 rounded-lg bg-slate-100 p-3 font-mono text-xs">
                {finding.file}:{finding.line_start}
              </p>

              {finding.suggested_fix && (
                <div className="mt-3 rounded-lg bg-green-50 p-3 text-sm text-green-900">
                  <strong>Suggested fix:</strong> {finding.suggested_fix}
                </div>
              )}

              {finding.suggested_code && (
                <pre className="mt-3 overflow-auto rounded-lg bg-slate-950 p-3 text-xs text-white">
                  {finding.suggested_code}
                </pre>
              )}
            </article>
          ))
        )}
      </section>
    </div>
  );
}