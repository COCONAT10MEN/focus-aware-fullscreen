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

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import heal  # noqa: E402  (self-repair when Caelestia changes a little)

REL = os.path.join("services", "Kwin.qml")

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


def patched(text: str):
    """(patched text, whether an anchor had to be found ignoring whitespace)."""
    out, healed = text, False
    for anchor, body in INSERTIONS:
        count = out.count(anchor)
        if count == 1:
            out = out.replace(anchor, anchor + BEGIN + "\n" + body + END + "\n", 1)
            continue
        # Same lines with different spacing, found once: insert after them.
        tl = heal.lines(out)
        nt = [heal.norm(l) for l in tl]
        for a, b in heal._block_spans(out, TAG):
            for i in range(a, min(b, len(nt))):
                nt[i] = "\0"
        start = heal._find_normalized(tl, nt, [heal.norm(l) for l in heal.lines(anchor)])
        if start is None:
            short = anchor.strip().splitlines()[0]
            raise ValueError(f"anchor found {count} times: {short!r} (Caelestia changed; plugin needs updating)")
        end = start + len(heal.lines(anchor))
        out = "".join(tl[:end]) + BEGIN + "\n" + body + END + "\n" + "".join(tl[end:])
        healed = True
    if healed and not heal.parses(out):
        raise ValueError("could not adapt to this Caelestia safely (the result does not parse)")
    return out, healed


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
    if len(sys.argv) != 3 or sys.argv[1] not in ("apply", "revert", "status", "watchdog"):
        print(__doc__.strip())
        return 2
    action, shell_dir = sys.argv[1], sys.argv[2]
    heal.hold_shell_lock()  # other plugins patch at the same moment
    path = target(shell_dir)
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        print(f"FAILED: cannot read {path}: {e}")
        return 1

    def write_stock():
        with open(path, encoding="utf-8") as f:
            now = f.read()
        if strip(now) != now:
            write_atomic(path, strip(now))

    guard = heal.Guard(TAG, os.path.abspath(__file__), shell_dir, "Focus-aware Fullscreen")
    if action == "watchdog":
        print(guard.watchdog(write_stock))
        return 0

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
        want, healed = patched(clean)
        healed = [REL] if healed else []
        if guard.refused({REL: clean}, healed):
            raise ValueError("adapting to this Caelestia failed before, so it stays off until a plugin update")
    except ValueError as e:
        # Leave whatever is there untouched rather than half-patch the shell.
        print(f"FAILED: {e}")
        return 1
    if want == text:
        failed = guard.check(write_stock)
        if failed:
            print(failed)
            return 1
        print("OK")
        return 0
    write_atomic(path, want)
    with open(path, encoding="utf-8") as f:
        if f.read() != want:
            print("FAILED: write did not stick")
            return 1
    # Watch the file just patched: if Caelestia doesn't come back right, undo.
    guard.record({REL: clean}, [REL])
    print("PATCHED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
