import QtQuick
import Quickshell
import Quickshell.Io
import Caelestia
import qs.services
import "updater"

// Keeps services/Kwin.qml patched so the bar only hides for the window that
// actually has focus. Runs on every shell start; after a Caelestia update
// replaces the file, it patches it again and restarts the shell once.
Scope {
    id: root

    readonly property string pluginDir: decodeURIComponent(Qt.resolvedUrl(".").toString().replace(/^file:\/\//, "")).replace(/\/$/, "")

    // Restart the shell process (via its systemd service) instead of an
    // in-process reload, which can deadlock and does not restart plugins.
    function restartShell(): void {
        Quickshell.execDetached(["sh", root.pluginDir + "/restart-shell.sh", Quickshell.shellPath("shell.qml")]);
    }

    function handle(output: string): void {
        const result = output.trim();
        if (result === "PATCHED") {
            console.info("[focus-aware-fullscreen] patched Kwin.qml, restarting the shell");
            root.restartShell();
        } else if (result === "OK") {
            console.info("[focus-aware-fullscreen] patch already in place");
        } else if (result === "NOT_NEEDED") {
            // Caelestia 2.7.6+ already hides the bar only for the window on top.
            console.info("[focus-aware-fullscreen] built into this Caelestia, nothing to patch");
        } else {
            console.warn("[focus-aware-fullscreen] " + result);
            Toaster.toast(qsTr("Focus-aware fullscreen"), qsTr("Caelestia changed in its last update, so this is off for now. Checking for a fix..."), "warning");
            updater.checkNow();
        }
    }

    Process {
        running: true
        command: ["python3", "-I", root.pluginDir + "/patch.py", "apply", Quickshell.shellDir]
        stdout: StdioCollector {
            onStreamFinished: root.handle(text)
        }
    }

    // Plugin icon. Nexus draws font icons about 2px above centre, so the icon
    // is an SVG instead: the same Material Symbols glyph (fill 1, grade 25,
    // medium weight, as Nexus uses), centred by geometry. It is generated on
    // each machine from that user's live palette, never shipped: the
    // background is transparent (Nexus's own circle shows through) and only
    // the glyph takes the theme's on-container colour, rewritten on every
    // palette change. While the plugin is not running the file is removed,
    // so Nexus falls back to its own font icon instead of stale colours.
    readonly property string glyphPath: "M231.9 231.9H155.2Q135.5 231.9 122 245.5Q108.5 259.1 108.5 278.8Q108.5 298.5 122.1 312.1Q135.6 325.6 155.4 325.6H278.7Q298.4 325.6 312 312Q325.6 298.4 325.6 278.7V155.2Q325.6 135.5 312.1 122Q298.5 108.5 278.8 108.5Q259.1 108.5 245.5 122.1Q231.9 135.6 231.9 155.4ZM728.3 231.9V155.2Q728.3 135.5 714.8 122Q701.3 108.5 681.6 108.5Q661.9 108.5 648.3 122.1Q634.7 135.6 634.7 155.4V278.7Q634.7 298.4 648.3 312Q661.9 325.6 681.5 325.6H804.8Q824.5 325.6 838 312.1Q851.5 298.5 851.5 278.8Q851.5 259.1 838 245.5Q824.5 231.9 804.8 231.9ZM231.9 728.3V804.8Q231.9 824.5 245.5 838Q259.1 851.5 278.8 851.5Q298.5 851.5 312.1 838Q325.6 824.5 325.6 804.8V681.5Q325.6 661.9 312 648.3Q298.4 634.7 278.7 634.7H155.2Q135.5 634.7 122 648.3Q108.5 661.9 108.5 681.5Q108.5 701.3 122.1 714.8Q135.6 728.3 155.4 728.3ZM728.3 728.3H804.8Q824.5 728.3 838 714.8Q851.5 701.3 851.5 681.6Q851.5 661.9 838 648.3Q824.5 634.7 804.8 634.7H681.5Q661.9 634.7 648.3 648.3Q634.7 661.9 634.7 681.5V804.8Q634.7 824.5 648.3 838Q661.9 851.5 681.5 851.5Q701.3 851.5 714.8 838Q728.3 824.5 728.3 804.8Z"

    function hex(c: color): string {
        const h = v => Math.round(v * 255).toString(16).padStart(2, "0");
        return "#" + h(c.r) + h(c.g) + h(c.b);
    }

    readonly property string iconSvg: {
        const fg = Colours.palette.m3onSecondaryContainer;
        return '<svg xmlns="http://www.w3.org/2000/svg" width="192" height="192" viewBox="0 0 48 48">'
            + '<path transform="translate(12.3725 35.6275) scale(0.024224 -0.024224)" fill="' + hex(fg) + '" d="' + glyphPath + '"/>'
            + '</svg>\n';
    }

    onIconSvgChanged: iconFile.setText(iconSvg)
    Component.onCompleted: iconFile.setText(iconSvg)
    // Disabled, removed or shell quitting: drop the icon so it can never go
    // stale. The next start regenerates it before Nexus can be opened.
    Component.onDestruction: Quickshell.execDetached(["rm", "-f", root.pluginDir + "/icon.svg"])

    FileView {
        id: iconFile

        path: root.pluginDir + "/icon.svg"
        printErrors: false
    }

    // Opt-in updates: asks before changing anything (see updater/update.sh).
    Updater {
        id: updater

        pluginDir: root.pluginDir
    }
}
