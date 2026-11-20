# Focus-aware Fullscreen

A [Caelestia](https://github.com/caelestia-kde) plugin that fixes the bar
disappearing when you are *not* in a fullscreen app.

## The problem

Stock Caelestia hides the bar whenever **any** fullscreen window is on a
screen. Alt+Tab from a fullscreen game or video to a normal window and the bar
stays hidden, even though the window you are using is not fullscreen.

## What this plugin does

- The bar hides only when the window you are **actually using** is fullscreen.
- It stays steady while focus is moving (Alt+Tab, opening or closing the
  dashboard): no half-hide-then-bounce-back animation.
- With several monitors, a fullscreen app on one screen still hides the bar on
  that screen while you work on another.
- The volume/brightness pop-up, notifications and launcher shortcuts follow the
  same rule.

## Install

Nexus → Plugins → install from URL, paste:

```
https://github.com/COCONAT10MEN/focus-aware-fullscreen
```

Restart the shell when asked. On first start the plugin patches the bar and
restarts the shell once by itself.

Requires `python3` (preinstalled on almost every distro).

## How it works

Caelestia's plugin API has no hook for when the bar hides, so `main.qml` runs
`patch.py` on every shell start. The script inserts clearly marked blocks
(`// focus-aware-fullscreen:begin` … `:end`) into `services/Kwin.qml` of the
running shell. It is idempotent:

- already patched → does nothing;
- a Caelestia update replaced the file → patches it again and restarts the shell once
  (through its `caelestia-shell` systemd service; Quickshell's in-process reload
  can deadlock on current Caelestia and does not start plugins again);
- an update changed the code so the patch no longer fits → touches nothing and
  shows a toast saying the plugin needs updating.

## Uninstall

Disabling or removing the plugin does **not** undo the patch by itself (it would
stay until the next Caelestia update). Revert it first:

```bash
python3 ~/.config/caelestia/plugins/focus-aware-fullscreen/patch.py revert ~/.config/quickshell/caelestia
```

Then disable/remove the plugin in Nexus and restart the shell.

Check the current state:

```bash
python3 ~/.config/caelestia/plugins/focus-aware-fullscreen/patch.py status ~/.config/quickshell/caelestia
```

## License

[MIT](LICENSE): free for anyone to use, modify and redistribute, including in
other plugins or commercial projects. The only ask: if you use this as a base,
credit **[COCONAT10MEN](https://github.com/COCONAT10MEN)** (keeping the
LICENSE file's copyright line does that).
