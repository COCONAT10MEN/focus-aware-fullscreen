<div align="center">

<img src="assets/icon.svg" width="80" alt="Focus-aware Fullscreen icon" />

# focus-aware-fullscreen

[![Caelestia KDE](https://img.shields.io/badge/Caelestia_KDE-2.7.5_tested-9bd0cc?style=for-the-badge&labelColor=101418)](https://github.com/caelestia-kde/caelestia)
[![KDE Plasma](https://img.shields.io/badge/Plasma_6-1D99F3?logo=kde&logoColor=white&style=for-the-badge&labelColor=101418)](https://kde.org/plasma-desktop)
[![Version](https://img.shields.io/badge/Version-2.3.0-9bd0cc?style=for-the-badge&labelColor=101418)](metadata.json)
[![License: MIT](https://img.shields.io/badge/License-MIT-9bd0cc?style=for-the-badge&labelColor=101418)](LICENSE)

</div>

> [!NOTE]
> **Tested and working on Caelestia KDE 2.7.5.** Other versions may work too: if an
> update changes the code this plugin hooks into, it switches itself off safely and a
> notification tells you.

A plugin for [Caelestia KDE](https://github.com/caelestia-kde/caelestia) that stops the
bar from disappearing when you are *not* in a fullscreen app.

Stock Caelestia hides the bar whenever **any** fullscreen window is on a screen.
Alt+Tab from a fullscreen game or video to a normal window and the bar stays hidden,
even though the window you are using is not fullscreen.

## Installation

**Requirements:** Caelestia KDE (tested on 2.7.5), `python3`

**Easy install:** download the `…-UNZIP-then-double-click-Install.zip` file from the
[latest release](https://github.com/COCONAT10MEN/focus-aware-fullscreen/releases/latest), unzip it, and
double-click **Install Focus-aware Fullscreen** inside (choose *Execute* / *Run* if KDE asks). It copies the
plugin into place and restarts Caelestia. Every older version is on the
[Releases](https://github.com/COCONAT10MEN/focus-aware-fullscreen/releases) page with the same kind of zip.

**Or** open *Settings*, go to *Plugins*, and install from this URL:

```
https://github.com/COCONAT10MEN/focus-aware-fullscreen
```

On first start the plugin patches the bar and restarts the shell once by itself.

### Updating

From version 2.3.0 on, the plugin tells you when a new version is out, and never updates on
its own:

- About once a day it looks at this repository's
  [Releases](https://github.com/COCONAT10MEN/focus-aware-fullscreen/releases). Only releases are offered, never
  work-in-progress commits.
- When there is one, a notification says what changed and which Caelestia version it was
  tested on, with **Update**, **What's new** and **Skip this version**. Close it and it asks
  again in three days.
- If a release needs a newer Caelestia than yours, the notification says so and does not
  offer it until you update Caelestia.
- **Update** downloads that release, keeps your current version aside and restarts Caelestia.
  A notification then offers **Undo update**, which puts the previous version back (that
  release is then not offered again; newer ones are).

Installed before 2.3.0? Install from the same URL once more to get this.

Every version, with what changed and what it was tested on, is on the
[Releases](https://github.com/COCONAT10MEN/focus-aware-fullscreen/releases) page.

Turn update checks off (delete the file to turn them back on):

```bash
mkdir -p ~/.local/state/caelestia/plugin-updates/focus-aware-fullscreen && touch ~/.local/state/caelestia/plugin-updates/focus-aware-fullscreen/off
```

Undo the last update later:

```bash
bash ~/.config/caelestia/plugins/focus-aware-fullscreen/updater/update.sh rollback ~/.config/caelestia/plugins/focus-aware-fullscreen ~/.config/quickshell/caelestia
```

### Uninstalling

Disabling or removing the plugin does **not** undo the patch on its own (it would stay
until the next Caelestia update). Revert it first:

```bash
python3 ~/.config/caelestia/plugins/focus-aware-fullscreen/patch.py revert ~/.config/quickshell/caelestia
```

Then remove the plugin in *Settings -> Plugins* and restart the shell.

## What it changes

- The bar hides only when the window you are **actually using** is fullscreen
- It stays steady while focus moves (Alt+Tab, opening or closing the dashboard): no
  half-hide-then-bounce-back animation
- With several monitors, a fullscreen app on one screen still hides the bar on that
  screen while you work on another
- The volume/brightness pop-up, notifications and launcher shortcuts follow the same rule

## Configuring

Nothing to configure: enable the plugin and the bar follows the focused window.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| The bar still hides behind a fullscreen app | Check the patch is in place (below), then restart the shell |
| "Could not patch the bar after an update" notification | Caelestia changed the hooked code; nothing was touched. Check for a plugin update |
| Want to see what it is doing | Run `caelestia shell -l` and look for `[focus-aware-fullscreen]` lines |

Check the current state of the patch:

```bash
python3 ~/.config/caelestia/plugins/focus-aware-fullscreen/patch.py status ~/.config/quickshell/caelestia
```

## How it works

- Caelestia's plugin API has no hook for when the bar hides, so `main.qml` runs
  `patch.py` on every shell start. The script inserts clearly marked blocks
  (`// focus-aware-fullscreen:begin` … `:end`) into the running shell's
  `services/Kwin.qml`.
- Already patched -> it does nothing. A Caelestia update replaced the file -> it patches
  again and restarts the shell once, through its `caelestia-shell` systemd service. An
  update changed the code so the patch no longer fits -> it touches nothing and tells you.

## Repository layout

```
main.qml              plugin entry: applies the patch, draws the plugin icon
patch.py              idempotent, revertible patcher for services/Kwin.qml
restart-shell.sh      restarts the shell through its systemd service
assets/               README artwork
updater/              opt-in updates: update.sh (checks, asks, updates, undoes), Updater.qml
metadata.json         plugin manifest
```

## Credits

- [caelestia-kde](https://github.com/caelestia-kde/caelestia) by [ladybug-me](https://github.com/ladybug-me) and [0xSolanaceae](https://github.com/0xSolanaceae) - the shell and plugin system this builds on
- [COCONAT10MEN](https://github.com/COCONAT10MEN) - this plugin

## License

MIT - see [LICENSE](LICENSE). Free for anyone to use, modify and redistribute, including
in other plugins or commercial projects. If you use this as a base, please credit
[COCONAT10MEN](https://github.com/COCONAT10MEN) (keeping the LICENSE file's copyright
line does that).
