# rac

A private, fast, and beautiful browser for macOS, with Arc's best ideas,
Dia's calm, and optional AI that feels right.

rac is a fork of [helium-macos](https://github.com/imputnet/helium-macos),
built on [Helium](https://github.com/imputnet/helium). It tracks Helium's
releases and adds its own changes as a separate layer of patches on top.

> **Status:** early development. rac currently builds as stock Helium.
> See the [roadmap](docs/roadmap.md).

rac is an independent project. It isn't affiliated with or endorsed by
Helium, imput, or The Browser Company. Please don't report rac issues to
Helium.

## What rac is going for

- **Private:** no data collection, no accounts, no ads, ever.
- **Fast:** never slower than Helium.
- **Beautiful:** Arc's personality with Dia's simplicity.
- **Arc's best ideas:** spaces, favorites, pinned tabs, a sidebar that gets
  out of the way, a command bar, and boosts.
- **AI, only if you want it:** off by default, quiet when on. Still being
  designed.

Read the full [vision](VISION.md).

## How it works

rac builds Chromium from source in layers:

1. Chromium
2. [ungoogled-chromium](https://github.com/ungoogled-software/ungoogled-chromium) patches
3. Helium core patches (the `helium-chromium/` submodule)
4. Helium macOS patches
5. rac patches (`patches/rac/`)

Because rac keeps its changes in its own patches, picking up a new Helium
release means merging helium-macos and refreshing rac's patches. Details are
in the [docs](docs/README.md).

## Building

Follow [docs/building.md](docs/building.md), but clone rac instead of
helium-macos:

```sh
git clone --recurse-submodules https://github.com/notkainoa/rac.git
cd rac
./build.sh
```

You need macOS, Xcode, and over 100 GB of free disk space. A full build
takes several hours.

## Contributing

Contributions are welcome, including AI-assisted ones, as long as they're
tested and shown working. Read [CONTRIBUTING.md](CONTRIBUTING.md). Bugs,
ideas, and questions all go in [Issues](https://github.com/notkainoa/rac/issues).

## Credits

### Helium
rac is built on [Helium](https://github.com/imputnet/helium) and
[helium-macos](https://github.com/imputnet/helium-macos) by imput. Almost
everything that makes rac work is their work.

### ungoogled-chromium
Helium is based on
[ungoogled-chromium](https://github.com/ungoogled-software/ungoogled-chromium)
and
[ungoogled-chromium-macos](https://github.com/ungoogled-software/ungoogled-chromium-macos).

### Arc and Dia
rac's design is inspired by [Arc](https://arc.net) and
[Dia](https://diabrowser.com) from The Browser Company.

## License
rac is licensed under GPL-3.0, the same as Helium. See [LICENSE](LICENSE).

Content imported from other projects keeps its original license. For
example, unmodified code from ungoogled-chromium stays under its
[BSD 3-Clause license](LICENSE.ungoogled_chromium).
