#!/usr/bin/env python3
"""
Build a one-click briefing snapshot: the offline dashboard with the current
workbook's data pre-loaded, so it opens straight to the numbers with no upload.

Pipeline:
  1. (re)build the offline self-contained dashboard (fonts + SheetJS inlined)
  2. embed the workbook as base64 + a tiny bootstrap that feeds it through the
     dashboard's normal load path on page open

IMPORTANT: the output EMBEDS real operational data. It is written to gitignored
output/ and must only be shared over approved internal channels — never
committed. This builder script itself contains no data.

    python scripts/build_briefing_snapshot.py

Output -> output/VBX_Command_Center_Briefing.html  (gitignored — contains data)
"""
import base64
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OFFLINE = os.path.join(ROOT, "output", "VBX_Command_Center_Dashboard_offline.html")
WORKBOOK = os.path.join(ROOT, "output", "VBX_Command_Center_v1.xlsx")
OUT = os.path.join(ROOT, "output", "VBX_Command_Center_Briefing.html")

BOOT_TEMPLATE = """
<script>
/* ── Briefing snapshot: workbook embedded at build time ── */
(function () {
  var __WB__ = "%s";
  function bytes() {
    var bin = atob(__WB__), arr = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
    return arr;
  }
  function setStatus() {
    var s = document.getElementById("file-status");
    if (s) { s.textContent = "VBX_Command_Center_v1.xlsx"; s.className = "file-status loaded"; }
  }
  function boot() {
    try {
      // Preferred: drive the dashboard's own parse path directly (globals).
      if (typeof parseWorkbook === "function" && typeof XLSX !== "undefined") {
        var wb = XLSX.read(bytes(), { type: "array", cellDates: true });
        STATE.data = parseWorkbook(wb);
        setStatus();
        renderAll();
        return;
      }
      // Fallback: simulate a file upload through the input element.
      var file = new File([bytes()], "VBX_Command_Center_v1.xlsx",
        { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" });
      var input = document.getElementById("file-input");
      var dt = new DataTransfer(); dt.items.add(file); input.files = dt.files;
      input.dispatchEvent(new Event("change", { bubbles: true }));
    } catch (e) { console.error("Briefing auto-load failed:", e); }
  }
  // Run after the dashboard's own init() (registered earlier) has wired up.
  function deferred() { setTimeout(boot, 0); }
  if (document.readyState !== "loading") deferred();
  else document.addEventListener("DOMContentLoaded", deferred);
})();
</script>
"""


def main():
    if not os.path.exists(WORKBOOK):
        sys.exit(f"Workbook not found: {WORKBOOK}")

    # 1) ensure a fresh offline bundle
    print("Building offline base ...")
    subprocess.run([sys.executable, os.path.join(HERE, "build_offline_dashboard.py")],
                   check=True, cwd=ROOT)
    html = open(OFFLINE, encoding="utf-8").read()

    # 2) embed workbook + bootstrap just before </body>
    wb_b64 = base64.b64encode(open(WORKBOOK, "rb").read()).decode("ascii")
    boot = BOOT_TEMPLATE % wb_b64
    # NB: insert before the FINAL </body> — the inlined SheetJS blob contains
    # the literal substring "</body>", so a first-match replace would corrupt it.
    assert "</body>" in html, "no </body> in offline bundle"
    head, _, tail = html.rpartition("</body>")
    html = head + boot + "\n</body>" + tail

    open(OUT, "w", encoding="utf-8").write(html)
    print(f"\nWrote {OUT}  ({os.path.getsize(OUT)/1e6:.2f} MB)")
    print("⚠  Contains real data — share via approved internal channels only; never commit.")


if __name__ == "__main__":
    main()
