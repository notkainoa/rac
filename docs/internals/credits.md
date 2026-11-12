# Credits (rac://credits)

`rac://credits` is Chromium's `chrome://credits`. Release builds generate it
at build time: `components/resources/BUILD.gn` runs
`tools/licenses/licenses.py credits`, which walks the source tree and turns
each `third_party/<name>/README.chromium` into an entry showing that
project's name, link, and license text. `credits.patch` sets
`generate_about_credits = true` so dev builds get the real page instead of
`sample_credits.html`.

How an entry gets picked up:

- The scanner adds **every subdirectory of every directory named
  `third_party`, at any depth** — no wiring needed. That is why borrowed
  code lives in places like `chrome/browser/rac/power/third_party/ardia/`:
  the README.chromium and LICENSE beside it are what `rac://credits`
  displays.
- A license file that lives outside a `third_party/` dir can still be
  referenced: `License File:` accepts `../..` paths from the README's dir
  (rac's `third_party/cra/` entry points at
  `chrome/browser/rac/import/CRA_LICENSE`).
- When porting code into `chrome/browser/rac/...` without a `third_party/`
  dir (as the Arc importer does), add a top-level `third_party/<name>/`
  README.chromium entry in `patches/rac/credits/credits.patch` instead.
- The "source code is available" line under the entries is the
  `opensource_project`/`opensource_link` pair in `GenerateCredits` in
  `tools/licenses/licenses.py`; ungoogled-chromium pointed it at itself,
  Helium repointed it at Helium, and rac's patch repoints it at
  `github.com/notkainoa/rac`.

After adding an entry, rebuild and open `rac://credits` to confirm.
