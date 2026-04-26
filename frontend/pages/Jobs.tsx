import { useEffect, useState } from "react";
import { getJobs } from "../api/reviews";
import type { Job } from "../types/review";
import { Link } from "react-router-dom";

export function Jobs() {
  const [jobs, setJobs] = useState<Job[]>([]);

  async function loadJobs() {
    const data = await getJobs();
    setJobs(data);
  }

  useEffect(() => {
    loadJobs();
    const interval = setInterval(loadJobs, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      <section>
        <h1 className="text-3xl font-bold">Jobs</h1>
        <p className="mt-2 text-slate-600">
          Background review jobs currently stored in memory.
        </p>
      </section>

      <section className="overflow-hidden rounded-2xl bg-white shadow-sm">
        {jobs.length === 0 ? (
          <p className="p-5 text-slate-500">No jobs yet.</p>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-100 text-slate-600">
              <tr>
                <th className="p-3">Status</th>
                <th className="p-3">PR</th>
                <th className="p-3">Source</th>
                <th className="p-3">Review</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => (
                <tr key={job.job_id} className="border-t">
                  <td className="p-3 font-medium">{job.status}</td>
                  <td className="p-3">
                    <a
                      href={job.pr_url}
                      target="_blank"
                      className="text-blue-600 hover:underline"
                    >
                      Open PR
                    </a>
                  </td>
                  <td className="p-3">{job.source}</td>
                  <td className="p-3">
                    {job.review_id ? (
                      <Link
                        to={`/reviews/${job.review_id}`}
                        className="text-blue-600 hover:underline"
                      >
                        View review
                      </Link>
                    ) : (
                      "-"
                    )}
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