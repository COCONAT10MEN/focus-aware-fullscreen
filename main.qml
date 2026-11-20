import QtQuick
import Quickshell
import Quickshell.Io
import Caelestia

// Keeps services/Kwin.qml patched so the bar only hides for the window that
// actually has focus. Runs on every shell start; after a Caelestia update
// replaces the file, it patches it again and reloads the shell once.
Scope {
    id: root

    readonly property string pluginDir: decodeURIComponent(Qt.resolvedUrl(".").toString().replace(/^file:\/\//, "")).replace(/\/$/, "")

    function handle(output: string): void {
        const result = output.trim();
        if (result === "PATCHED") {
            console.info("[focus-aware-fullscreen] patched Kwin.qml, reloading shell");
            Quickshell.reload(false);
        } else if (result === "OK") {
            console.info("[focus-aware-fullscreen] patch already in place");
        } else {
            console.warn("[focus-aware-fullscreen] " + result);
            Toaster.toast(qsTr("Focus-aware fullscreen"), qsTr("Could not patch the bar after an update: %1").arg(result), "warning");
        }
    }

    Process {
        running: true
        command: ["python3", "-I", root.pluginDir + "/patch.py", "apply", Quickshell.shellDir]
        stdout: StdioCollector {
            onStreamFinished: root.handle(text)
        }
    }
}
