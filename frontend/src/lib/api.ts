export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    headers: { 'content-type': 'application/json' },
    ...init
  });
  if (!res.ok) {
    throw new Error(`${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export type Stats = {
  works: number;
  assets: number;
  tags: number;
  review_queue: number;
};

export type Work = {
  id: number;
  title: string;
  sort_author: string;
  series: string | null;
  series_position: number | null;
  publication_year: number | null;
  audience: string | null;
  identifiers: Record<string, unknown>;
};

export type Tag = {
  id: number;
  slug: string;
  label: string;
  color: string | null;
  is_filter: boolean;
};

export type LibraryRoot = {
  id: number;
  kind: string;
  path: string;
  enabled: boolean;
  last_scanned_at: string | null;
};

export type ReviewItem = {
  id: number;
  asset_id: number;
  candidate_work_id: number | null;
  confidence: number;
  reasons: Record<string, unknown>;
  status: string;
};
