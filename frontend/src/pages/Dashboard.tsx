import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getHealth, getReviews } from "../api/reviews";
import type { ReviewSummary } from "../types/review";

export function Dashboard() {
  const [reviews, setReviews] = useState<ReviewSummary[]>([]);
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  async function loadData() {
    setLoading(true);
    const [healthData, reviewData] = await Promise.all([
      getHealth(),
      getReviews(50),
    ]);
    setHealth(healthData);
    setReviews(reviewData);
    setLoading(false);
  }

  useEffect(() => {
    loadData().catch(console.error);
  }, []);

  if (loading) {
    return <p>Loading dashboard...</p>;
  }

  return (
    <div className="space-y-6">
      <section>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="mt-2 text-slate-600">
          Review history from your AI Merge Guard backend.
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <div className="rounded-2xl bg-white p-5 shadow-sm">
          <p className="text-sm text-slate-500">Backend</p>
          <p className="mt-1 text-xl font-semibold">{health?.status}</p>
        </div>

        <div className="rounded-2xl bg-white p-5 shadow-sm">
          <p className="text-sm text-slate-500">GitHub App</p>
          <p className="mt-1 text-xl font-semibold">
            {health?.github_app_configured ? "Configured" : "Not configured"}
          </p>
        </div>

        <div className="rounded-2xl bg-white p-5 shadow-sm">
          <p className="text-sm text-slate-500">LLM</p>
          <p className="mt-1 text-xl font-semibold">
            {health?.llm_enabled ? "Enabled" : "Disabled"}
          </p>
        </div>
      </section>

      <section className="overflow-hidden rounded-2xl bg-white shadow-sm">
        <div className="border-b px-5 py-4">
          <h2 className="font-semibold">Recent Reviews</h2>
        </div>

        {reviews.length === 0 ? (
          <p className="p-5 text-slate-500">No reviews yet.</p>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-100 text-slate-600">
              <tr>
                <th className="p-3">Repo</th>
                <th className="p-3">PR</th>
                <th className="p-3">Conclusion</th>
                <th className="p-3">Findings</th>
                <th className="p-3">Source</th>
                <th className="p-3">Created</th>
              </tr>
            </thead>
            <tbody>
              {reviews.map((review) => (
                <tr key={review.review_id} className="border-t">
                  <td className="p-3 font-medium">
                    <Link
                      className="text-blue-600 hover:underline"
                      to={`/reviews/${review.review_id}`}
                    >
                      {review.repo_full_name}
                    </Link>
                  </td>
                  <td className="p-3">
                    <a
                      href={review.pr_url}
                      target="_blank"
                      className="text-blue-600 hover:underline"
                    >
                      #{review.pr_number}
                    </a>
                  </td>
                  <td className="p-3">{review.conclusion}</td>
                  <td className="p-3">{review.findings_count}</td>
                  <td className="p-3">{review.source}</td>
                  <td className="p-3">
                    {new Date(review.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}