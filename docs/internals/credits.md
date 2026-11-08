# Credits (rac://credits)

`rac://credits` is Chromium's `chrome://credits`, generated at build time by
`tools/licenses/licenses.py credits` in `build/src`. The
`components/resources:about_credits` GN action scans the tree for
`third_party/**/README.chromium` files and turns each one plus its license
file into an entry. rac's `stable/credits.patch` sets
`generate_about_credits = true` so dev builds get the real page instead of
`sample_credits.html`, and points the reciprocal "source code is available"
link at `notkainoa/rac`.

What makes an entry:

- **`third_party/<name>/README.chromium`** — the metadata scanner's input.
  rac's own entry is `third_party/rac/` (`README.chromium` + the GPL-3.0
  `LICENSE`). Code a feature ports or copies from another project gets the
  same pair in its own `third_party/` dir (see
  `chrome/browser/rac/power/third_party/` for existing examples).
- **`tools/licenses/licenses.py`** — the metadata blocks at the top
  (`_CHROMIUM_LICENSE_METADATA`, `_UGC_LICENSE_METADATA`) for projects whose
  license file can't be discovered by the scan, and the reciprocal
  statement in `GenerateCredits`.
- **Templates** — `components/webui/about/resources/about_credits*.tmpl`
  shape the page; ungoogled's `add-credits.patch` and Helium's
  `update-credits.patch` show how the pipeline has been rebranded before.

After adding a `third_party/` dir, rebuild and open `rac://credits` to check
the entry appears.
