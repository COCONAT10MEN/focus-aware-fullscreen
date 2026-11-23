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

Grab the zip from the [latest release](https://github.com/COCONAT10MEN/focus-aware-fullscreen/releases/latest), unzip it and double-click
**Install** inside. That's it. Older versions are on the [Releases](https://github.com/COCONAT10MEN/focus-aware-fullscreen/releases) page too.

Or paste this into Caelestia's *Settings → Plugins*:

```
https://github.com/COCONAT10MEN/focus-aware-fullscreen
```

On first start the plugin patches the bar and restarts the shell once by itself.

### Updating

It checks for new releases about once a day. When one's out you get a notification saying
what's new and which Caelestia it was tested on: hit **Update**, or **Skip this one**. It never
updates by itself, and right after an update there's an **Undo** in case something breaks.

On a version older than 2.3.0? Reinstall it once to get this.

Don't want the checks?

```bash
mkdir -p ~/.local/state/caelestia/plugin-updates/focus-aware-fullscreen && touch ~/.local/state/caelestia/plugin-updates/focus-aware-fullscreen/off
```

Want the previous version back later?

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
updater/              update checks (always asks first)
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
