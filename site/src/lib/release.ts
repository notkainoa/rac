import { RELEASE_READY, REPO_URL } from "../config";

// The download page's data: the latest GitHub release, read once at build
// time. Visitors never talk to GitHub's API; their browser only fetches the
// disk image they pick. Until RELEASE_READY is true there's no release, so the
// page shows SAMPLE instead.

// rac is built for Apple silicon only. A release may still carry other
// disk images; the site only ever offers the arm64 one.
export const PLATFORM = "Apple silicon (M1 or later), macOS 13 Ventura or later";

export interface Build {
  label: string;
  file: string;
  url: string;
  size: number;
  sha256?: string;
}

export interface Release {
  version: string;
  date: string;
  notesUrl: string;
  build: Build;
  // Versions before 0.2.0 are quiet previews, labelled on the page.
  preview: boolean;
  sample: boolean;
}

const isPreview = (version: string) => {
  const [major = 0, minor = 0] = version.replace(/^v/, "").split(".").map(Number);
  return major === 0 && minor < 2;
};

// Made-up numbers in the shape of a real release. The links go to the
// releases page, so nobody downloads a file that doesn't exist.
const SAMPLE: Release = {
  version: "0.1.0",
  date: "2026-11-06T18:00:00Z",
  notesUrl: `${REPO_URL}/releases`,
  preview: true,
  sample: true,
  build: {
    label: "Apple silicon",
    file: "rac_0.1.0_arm64-macos.dmg",
    url: `${REPO_URL}/releases`,
    size: 214_806_528,
    sha256: "9f2c4e71a0b85d36e1f47c2a9b0d58e3c61f7a24d95b0e83c7a1f6d42e9b5c08",
  },
};

interface GitHubAsset {
  name: string;
  size: number;
  browser_download_url: string;
  digest?: string | null;
}

interface GitHubRelease {
  tag_name: string;
  published_at: string;
  html_url: string;
  assets: GitHubAsset[];
}

let cached: Promise<Release> | undefined;

export function getRelease(): Promise<Release> {
  cached ??= RELEASE_READY ? fetchLatest() : Promise.resolve(SAMPLE);
  return cached;
}

// A failed fetch fails the build on purpose: Vercel keeps the last good
// deployment live rather than shipping a page with broken links.
async function fetchLatest(): Promise<Release> {
  const repo = new URL(REPO_URL).pathname.slice(1);
  const headers: Record<string, string> = { Accept: "application/vnd.github+json" };
  // Optional, but builds without it share GitHub's low anonymous rate limit.
  const token = (globalThis as { process?: { env: Record<string, string | undefined> } }).process?.env.GITHUB_TOKEN;
  if (token) headers.Authorization = `Bearer ${token}`;
  // releases/latest skips drafts and prereleases, the same rule the update
  // feed follows, so the page and installed copies always agree.
  const res = await fetch(`https://api.github.com/repos/${repo}/releases/latest`, { headers });
  if (!res.ok) throw new Error(`GitHub releases API answered ${res.status}`);
  const data = (await res.json()) as GitHubRelease;

  // build.yml names the disk images rac_<version>_<arch>-macos.dmg.
  const asset = data.assets.find((a) => a.name.endsWith("_arm64-macos.dmg"));
  if (!asset) throw new Error(`Release ${data.tag_name} has no arm64 disk image`);

  return {
    version: data.tag_name,
    date: data.published_at,
    notesUrl: data.html_url,
    preview: isPreview(data.tag_name),
    sample: false,
    build: {
      label: "Apple silicon",
      file: asset.name,
      url: asset.browser_download_url,
      size: asset.size,
      sha256: asset.digest?.startsWith("sha256:") ? asset.digest.slice(7) : undefined,
    },
  };
}
