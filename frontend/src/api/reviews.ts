import { api } from "./client";
import type { Job, ReviewDetail, ReviewSummary } from "../types/review";

export async function getHealth() {
  const res = await api.get("/health");
  return res.data;
}

export async function getReviews(limit = 25): Promise<ReviewSummary[]> {
  const res = await api.get(`/history/reviews?limit=${limit}`);
  return res.data.reviews;
}

export async function getReview(reviewId: string): Promise<ReviewDetail> {
  const res = await api.get(`/history/reviews/${reviewId}`);
  return res.data;
}

export async function startReview(prUrl: string, installationId?: number | null) {
  const res = await api.post("/review-pr/async", {
    pr_url: prUrl,
    installation_id: installationId ?? null,
  });

  return res.data as {
    ok: boolean;
    job_id: string;
    status: string;
  };
}

export async function getJob(jobId: string): Promise<Job> {
  const res = await api.get(`/jobs/${jobId}`);
  return res.data;
}

export async function getJobs(): Promise<Job[]> {
  const res = await api.get("/jobs");
  return res.data.jobs;
}