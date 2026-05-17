export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    headers: { 'content-type': 'application/json' },
    ...init
  });
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (body && typeof body === 'object' && 'detail' in body) {
        detail = String((body as { detail: unknown }).detail);
      }
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export type Stats = {
  works: number;
  assets: number;
  tags: number;
  review_queue: number;
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
  kind: 'ebook' | 'audiobook';
  path: string;
  enabled: boolean;
  last_scanned_at: string | null;
  path_exists: boolean;
  path_is_directory: boolean;
};

export type WorkListItem = {
  id: number;
  title: string;
  sort_author: string;
  series: string | null;
  series_position: number | null;
  publication_year: number | null;
  audience: string | null;
  ebook_count: number;
  audiobook_count: number;
  authors: string[];
  tags: Tag[];
};

export type WorkListResponse = {
  total: number;
  limit: number;
  offset: number;
  items: WorkListItem[];
};

export type Asset = {
  id: number;
  type: string;
  format: string | null;
  path: string | null;
  source_kind: string;
  size_bytes: number | null;
  duration_seconds: number | null;
  page_count: number | null;
  bitrate: number | null;
  narrator: string | null;
  metadata_blob: Record<string, unknown>;
  first_seen: string;
  last_seen: string;
};

export type WorkDetail = {
  id: number;
  title: string;
  normalized_title: string;
  sort_author: string;
  authors: string[];
  series: string | null;
  series_position: number | null;
  publication_year: number | null;
  audience: string | null;
  identifiers: Record<string, string>;
  notes: string | null;
  tags: Tag[];
  assets: Asset[];
};

export type ReviewItem = {
  id: number;
  asset_id: number;
  candidate_work_id: number | null;
  confidence: number;
  reasons: Record<string, unknown>;
  status: string;
};

export type ScanRootResult = {
  library_root_id: number;
  path: string;
  kind: string;
  files_seen: number;
  assets_added: number;
  assets_updated: number;
  works_created: number;
  review_items_created: number;
  errors: string[];
};

export type ScanStatus = {
  running: boolean;
  started_at: string | null;
  finished_at: string | null;
  current_root_id: number | null;
  current_root_path: string | null;
  results: ScanRootResult[];
  error: string | null;
};

export const COVERAGE_OPTIONS = [
  { value: 'all', label: 'All works' },
  { value: 'complete', label: 'Complete (both formats)' },
  { value: 'missing_audiobook', label: 'Missing audiobook' },
  { value: 'missing_ebook', label: 'Missing ebook' },
  { value: 'has_ebook', label: 'Has ebook' },
  { value: 'has_audiobook', label: 'Has audiobook' },
  { value: 'orphan', label: 'No assets' }
] as const;

export const AUDIENCE_OPTIONS = [
  { value: 'adult', label: 'Adult' },
  { value: 'ya', label: 'YA' },
  { value: 'middle-grade', label: 'Middle grade' },
  { value: 'kids', label: 'Kids' },
  { value: 'picture-book', label: 'Picture book' }
] as const;

export function formatDuration(seconds: number | null | undefined): string {
  if (!seconds) return '—';
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

export function formatBytes(bytes: number | null | undefined): string {
  if (!bytes) return '—';
  const units = ['B', 'KB', 'MB', 'GB'];
  let i = 0;
  let v = bytes;
  while (v >= 1024 && i < units.length - 1) {
    v /= 1024;
    i++;
  }
  return `${v.toFixed(v >= 10 || i === 0 ? 0 : 1)} ${units[i]}`;
}
