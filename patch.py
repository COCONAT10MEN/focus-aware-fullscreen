#!/usr/bin/env python3
"""Focus-aware fullscreen patcher for the Caelestia shell.

Caelestia hides the bar whenever *any* fullscreen window sits on a screen,
even when a normal window in front of it has focus. Its plugin system has no
hook for that logic, so this script inserts a small, clearly marked block into
services/Kwin.qml. It is idempotent: the plugin runs it on every shell start,
so a Caelestia update that replaces Kwin.qml simply gets patched again.

Usage:
    patch.py apply  <shell dir>   -> prints OK | PATCHED | NOT_NEEDED | FAILED: <reason>
    patch.py revert <shell dir>   -> prints REVERTED | NOTHING
    patch.py status <shell dir>   -> prints APPLIED | OUTDATED | MISSING | NOT_NEEDED

Caelestia 2.7.6 and newer hide the bar by the topmost window on each screen
(the compositor's fullscreenOutputs), which already does what this plugin is
for. There the patcher removes any old block and reports NOT_NEEDED.
"""

import os
import re
import sys
import tempfile

VERSION = "2"
TAG = "focus-aware-fullscreen"
BEGIN = f"// {TAG}:begin v{VERSION}"
END = f"// {TAG}:end"
BLOCK_RE = re.compile(
    r"^[ \t]*// " + re.escape(TAG) + r":begin[^\n]*\n.*?^[ \t]*// " + re.escape(TAG) + r":end[^\n]*\n",
    re.S | re.M,
)

# Each insertion goes right after an anchor that must appear exactly once.
INSERTIONS = [
    (
        # Remember the last real window that had focus. KWin clears the active
        # window for a moment while focus moves (Alt+Tab, the dashboard or
        # launcher taking keyboard focus); without this the bar briefly thinks
        # a fullscreen window is in charge, starts hiding, then bounces back.
        "    readonly property var windowList: KWinActiveWindowBridge.windowList || []\n",
        """    property string faLastFocusAddr: ""
    onActiveWindowChanged: {
        const w = root.activeWindow;
        const addr = String(w?.address ?? "");
        if (addr.length > 0 && !root.isIgnoredWindow(w))
            root.faLastFocusAddr = addr;
    }
    // The window the user is actually working in: the active one, or the last
    // real one while focus is in transit. Null when it is gone or minimized.
    function faFocusedWindow(): var {
        const active = root.activeWindow;
        let addr = String(active?.address ?? "");
        if (addr.length === 0 || root.isIgnoredWindow(active))
            addr = root.faLastFocusAddr;
        if (addr.length === 0)
            return null;
        const wins = root.windowList;
        for (let i = 0; i < wins.length; i++) {
            if (String(wins[i].address ?? "") === addr)
                return wins[i].minimized ? null : wins[i];
        }
        return null;
    }
""",
    ),
    (
        "    function hasFullscreen(): bool {\n"
        "        const wins = root.windowList;\n"
        "        const activeWs = root.activeWsId;\n",
        """        const faWin = root.faFocusedWindow();
        if (faWin) {
            const faWs = faWin.workspace?.id ?? -1;
            if (activeWs === -1 || faWs === -1 || faWs === activeWs)
                return faWin.fullscreen === true;
        }
""",
    ),
    (
        "    function hasFullscreenOn(screenName: string): bool {\n"
        "        if (!screenName)\n"
        "            return hasFullscreen();\n"
        "        const wins = root.windowList;\n"
        "        const activeWs = root.activeWsId;\n",
        """        // A focused window on this screen decides; only fall back to "any
        // fullscreen window here" when focus is on another screen.
        const faWin = root.faFocusedWindow();
        if (faWin && faWin.output === screenName) {
            const faWs = faWin.workspace?.id ?? -1;
            if (activeWs === -1 || faWs === -1 || faWs === activeWs)
                return faWin.fullscreen === true;
        }
""",
    ),
]


def target(shell_dir: str) -> str:
    return os.path.join(shell_dir, "services", "Kwin.qml")


def strip(text: str) -> str:
    return BLOCK_RE.sub("", text)


def built_in(text: str) -> bool:
    """Caelestia already hides the bar only for the window on top (2.7.6+)."""
    return "KWinActiveWindowBridge.fullscreenOutputs" in text


def patched(text: str) -> str:
    out = text
    for anchor, body in INSERTIONS:
        count = out.count(anchor)
        if count != 1:
            short = anchor.strip().splitlines()[0]
            raise ValueError(f"anchor found {count} times: {short!r} (Caelestia changed; plugin needs updating)")
        out = out.replace(anchor, anchor + BEGIN + "\n" + body + END + "\n", 1)
    return out


def write_atomic(path: str, text: str) -> None:
    st = os.stat(path)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".Kwin.qml.")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.chmod(tmp, st.st_mode & 0o7777)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] not in ("apply", "revert", "status"):
        print(__doc__.strip())
        return 2
    action, shell_dir = sys.argv[1], sys.argv[2]
    path = target(shell_dir)
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        print(f"FAILED: cannot read {path}: {e}")
        return 1

    has_current = BEGIN in text
    has_any = BLOCK_RE.search(text) is not None
    clean = strip(text)

    if action == "status":
        if built_in(clean) and not has_any:
            print("NOT_NEEDED")
        else:
            print("APPLIED" if has_current else ("OUTDATED" if has_any else "MISSING"))
        return 0

    if action == "revert":
        if not has_any:
            print("NOTHING")
            return 0
        write_atomic(path, clean)
        print("REVERTED")
        return 0

    # apply
    if built_in(clean):
        if has_any:
            write_atomic(path, clean)
            print("PATCHED")
        else:
            print("NOT_NEEDED")
        return 0
    try:
        want = patched(clean)
    except ValueError as e:
        # Leave whatever is there untouched rather than half-patch the shell.
        print(f"FAILED: {e}")
        return 1
    if want == text:
        print("OK")
        return 0
    write_atomic(path, want)
    with open(path, encoding="utf-8") as f:
        if f.read() != want:
            print("FAILED: write did not stick")
            return 1
    print("PATCHED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
