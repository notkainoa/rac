import { RELEASE_READY, REPO_URL } from "../config";

// The download page's data: the latest GitHub release, read once at build
// time. Visitors never talk to GitHub's API; their browser only fetches the
// disk image they pick. Until RELEASE_READY is true there's no release, so the
// page shows SAMPLE instead.

export type Arch = "arm64" | "x86_64";

export interface Build {
  arch: Arch;
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
  builds: Build[];
  sample: boolean;
}

const LABELS: Record<Arch, string> = { arm64: "Apple silicon", x86_64: "Intel" };

// Made-up numbers in the shape of a real release. The links go to the
// releases page, so nobody downloads a file that doesn't exist.
const SAMPLE: Release = {
  version: "0.1.0",
  date: "2026-11-03T18:00:00Z",
  notesUrl: `${REPO_URL}/releases`,
  sample: true,
  builds: [
    {
      arch: "arm64",
      label: LABELS.arm64,
      file: "rac_0.1.0_arm64-macos.dmg",
      url: `${REPO_URL}/releases`,
      size: 214_806_528,
      sha256: "9f2c4e71a0b85d36e1f47c2a9b0d58e3c61f7a24d95b0e83c7a1f6d42e9b5c08",
    },
    {
      arch: "x86_64",
      label: LABELS.x86_64,
      file: "rac_0.1.0_x86_64-macos.dmg",
      url: `${REPO_URL}/releases`,
      size: 226_492_416,
      sha256: "3b7e0d9a1c64f2e85a09b7d3c1e6f4a28d5b9c07e3f1a6d42b8c5e09f7a3d61c",
    },
  ],
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
  if (process.env.GITHUB_TOKEN) headers.Authorization = `Bearer ${process.env.GITHUB_TOKEN}`;
  const res = await fetch(`https://api.github.com/repos/${repo}/releases/latest`, { headers });
  if (!res.ok) throw new Error(`GitHub releases API answered ${res.status}`);
  const data = (await res.json()) as GitHubRelease;

  // build.yml names the disk images rac_<version>_<arch>-macos.dmg.
  const builds = (["arm64", "x86_64"] as const).map((arch): Build => {
    const asset = data.assets.find((a) => a.name.endsWith(`_${arch}-macos.dmg`));
    if (!asset) throw new Error(`Release ${data.tag_name} has no ${arch} disk image`);
    return {
      arch,
      label: LABELS[arch],
      file: asset.name,
      url: asset.browser_download_url,
      size: asset.size,
      sha256: asset.digest?.startsWith("sha256:") ? asset.digest.slice(7) : undefined,
    };
  });

  return { version: data.tag_name, date: data.published_at, notesUrl: data.html_url, builds, sample: false };
}
