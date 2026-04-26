import { useEffect, useState } from "react";
import { startReview, getJob } from "../api/reviews";
import type { Job } from "../types/review";
import { Link } from "react-router-dom";

export function ManualReview() {
  const [prUrl, setPrUrl] = useState("");
  const [installationId, setInstallationId] = useState("");
  const [jobId, setJobId] = useState<string | null>(null);
  const [job, setJob] = useState<Job | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function submitReview(event: React.FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setJob(null);

    const result = await startReview(
      prUrl,
      installationId ? Number(installationId) : null
    );

    setJobId(result.job_id);
    setSubmitting(false);
  }

  useEffect(() => {
    if (!jobId) return;

    const interval = setInterval(async () => {
      const latestJob = await getJob(jobId);
      setJob(latestJob);

      if (latestJob.status === "completed" || latestJob.status === "failed") {
        clearInterval(interval);
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [jobId]);

  return (
    <div className="max-w-2xl space-y-6">
      <section>
        <h1 className="text-3xl font-bold">Manual PR Review</h1>
        <p className="mt-2 text-slate-600">
          Paste a GitHub pull request URL and ask Merge Guard to review it.
        </p>
      </section>

      <form onSubmit={submitReview} className="space-y-4 rounded-2xl bg-white p-5 shadow-sm">
        <div>
          <label className="block text-sm font-medium">Pull request URL</label>
          <input
            value={prUrl}
            onChange={(e) => setPrUrl(e.target.value)}
            placeholder="https://github.com/org/repo/pull/123"
            required
            className="mt-1 w-full rounded-lg border px-3 py-2"
          />
        </div>

        <div>
          <label className="block text-sm font-medium">
            Installation ID optional
          </label>
          <input
            value={installationId}
            onChange={(e) => setInstallationId(e.target.value)}
            placeholder="Leave empty if using GITHUB_TOKEN"
            className="mt-1 w-full rounded-lg border px-3 py-2"
          />
        </div>

        <button
          disabled={submitting}
          className="rounded-lg bg-slate-900 px-4 py-2 font-medium text-white disabled:opacity-50"
        >
          {submitting ? "Starting..." : "Start Review"}
        </button>
      </form>

      {jobId && (
        <section className="rounded-2xl bg-white p-5 shadow-sm">
          <h2 className="font-semibold">Job Status</h2>
          <p className="mt-2 text-sm text-slate-600">Job ID: {jobId}</p>
          <p className="mt-2 text-lg font-bold">
            {job ? job.status : "queued"}
          </p>

          {job?.error && (
            <p className="mt-3 rounded-lg bg-red-50 p-3 text-sm text-red-800">
              {job.error}
            </p>
          )}

          {job?.review_id && (
            <Link
              to={`/reviews/${job.review_id}`}
              className="mt-4 inline-block rounded-lg bg-blue-600 px-4 py-2 text-white"
            >
              View Review
            </Link>
          )}
        </section>
      )}
    </div>
  );
}