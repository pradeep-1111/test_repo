export type ReviewSummary = {
  review_id: number;
  repo_full_name: string;
  pr_number: number;
  pr_url: string;
  head_sha: string;
  conclusion: string;
  findings_count: number;
  source: string;
  created_at: string;
};

export type Finding = {
  category: string;
  title: string;
  severity: string;
  file: string;
  line_start: number;
  line_end: number;
  explanation: string;
  confidence: number;
  suggested_fix?: string | null;
  suggested_code?: string | null;
  source: string;
};

export type ReviewDetail = ReviewSummary & {
  summary_markdown: string;
  tool_warnings: string[];
  findings: Finding[];
};

export type Job = {
  job_id: string;
  pr_url: string;
  installation_id?: number | null;
  source: string;
  status: "queued" | "running" | "completed" | "failed";
  created_at: string;
  started_at?: string | null;
  finished_at?: string | null;
  review_id?: number | null;
  error?: string | null;
};