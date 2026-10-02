# rac vision

rac is a private, fast, and beautiful browser for macOS. It has Arc's best
ideas and Dia's calm, and an optional AI that feels right when you want it and
stays out of the way when you don't.

rac is built on [Helium](https://github.com/imputnet/helium), which is built on
[ungoogled-chromium](https://github.com/ungoogled-software/ungoogled-chromium).
Helium provides privacy and speed. rac adds the interface, features, and
polish on top.

The name is "arc" backwards. It's written in lowercase: **rac**.

## Why rac exists

Arc changed how browsing felt, then got buggy, glitchy, and slow, and
eventually stopped being developed. Dia was clean and calm, but not agentic
enough. Aside could actually control the browser, but it felt slow and
cluttered. Helium is private, fast, and clean enough, but plain. Most
browsers that copy Arc feel unfinished and slow. The few with AI do it badly.

rac is the browser that should exist: Helium's privacy and speed, Arc's
features and beauty, Dia's simplicity, and AI that is genuinely useful without
being in your face. It's also open source, because a browser sees everything
you do, and you should be able to read its code.

## Who it's for

rac is the maintainer's daily driver first. It's kept up to date with Helium
and improved continuously. Everyone else is welcome, especially:

- former Arc users looking for a replacement
- Helium users who want a nicer interface
- anyone who wants a browser that feels good to use

## What rac never compromises on

1. **Private.** rac never sees, keeps, or sells your data. There are no rac
   accounts, no rac servers holding your browsing, no ads, and no sponsored
   content. When you use AI, your chosen provider's terms apply between you
   and that provider. rac itself never sees your conversations.
2. **Never slower than Helium.** Every feature has to earn its place without
   slowing startup, tab switching, scrolling, or typing. Features that are
   turned off cost nothing: no background work, no network calls, no
   processes.
3. **Beautiful and calm.** Arc's playful color and personality, combined
   with Dia's simplicity and elegance. Tasteful micro-interactions that make
   the browser feel alive, never animation for its own sake.
4. **Opinionated.** Like Arc and Dia, rac picks good defaults instead of
   offering a setting for everything. A setting exists only when people
   genuinely need different behavior.
5. **AI is optional and quiet.** AI is off until you turn it on. When it's
   on, it shows up only where it's useful. It shows what it's doing in a
   calm, minimal way, and it never takes an action you didn't ask for.
6. **Open.** rac is GPL-3.0, developed in the open, and tracks Helium
   closely instead of drifting into a separate codebase.

## How rac works

### Profiles, spaces, and tabs

- **Each profile opens in its own window,** the same as in Helium. Profiles
  keep logins, cookies, and data separate.
- **Each profile has its own spaces.** A space is a separate set of tabs with
  its own color theme and icon. You switch spaces with the dots at the bottom
  of the sidebar.
- **Favorites** sit at the top of the sidebar as icons. They are shared by
  every space in a profile. Helium calls these "pinned" today.
- **Pinned tabs** are Arc-style. They live in the sidebar of one space, stay
  there permanently, and are separate from that space's regular open tabs.

### The sidebar

- Tabs live in a vertical sidebar, building on Helium's vertical layout.
- **Cmd+S fully hides and shows the sidebar** by default. A setting switches
  Cmd+S back to Helium's behavior, which collapses the sidebar to a compact
  strip of site icons.
- Moving the mouse to the left or top edge of the screen reveals the hidden
  sidebar or toolbar. This builds on Helium's existing behavior and makes it
  feel polished.
- An appearance setting moves the address bar into the sidebar.

### Everything else

- **Command bar:** a quick launcher for tabs, history, and actions. You can
  choose it in place of the regular new tab page.
- **Boosts:** restyle any website with your own CSS and JavaScript.
- **Space themes:** gradient color themes, one per space.
- **Split view:** several tabs side by side (Helium has this today).
- **Picture-in-picture** that pops out automatically when you leave a tab
  with a playing video.
- **Media controls** in the sidebar.

### AI

AI is a core part of where rac is going, but **how it works is not decided
yet.** These points are settled:

- AI is off by default. Onboarding asks whether you want it, and you can
  change your answer in settings at any time.
- When AI is off, none of its code does any work.
- rac never sees your AI conversations, and rac doesn't run its own AI
  servers.
- The AI never takes an action in your browser without your confirmation.

Everything else, including providers, features, the agent, and safety
checks, will be designed properly when it's built. Ideas collected so far
are in [docs/internals/ai.md](docs/internals/ai.md).

## What rac will never do

- Collect, keep, sell, or look at your data
- Show ads or sponsored content
- Require an account
- Include a built-in VPN
- Include crypto features

## Not planned for now

These aren't ruled out forever, just not on the roadmap:

- Auto-archiving old tabs
- Peek-style link previews in a floating window
- A settings page for everything
- Sync (maybe later)
- Linux and Windows (maybe someday)
- iOS (probably someday)

## Relationship with Helium

rac follows Helium releases closely, and all of rac's changes sit on top of
Helium as a separate layer. When Helium adds something rac also built, rac
should consider adopting Helium's version. rac is an independent project. It
is not affiliated with Helium, and rac issues and contributions never go to
Helium's repositories.

See the [roadmap](docs/roadmap.md) for the order in which this gets built.
