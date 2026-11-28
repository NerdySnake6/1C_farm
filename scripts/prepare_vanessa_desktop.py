"""Prepare a NEW local farm base with the native Vanessa launcher configured."""
import argparse
import datetime as dt
import json
from pathlib import Path
import subprocess
import sys

from run_vanessa_tests import APP, ROOT, EPF_SHA256, digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--open", action="store_true", help="Open the prepared enterprise")
    args = parser.parse_args()
    release = ROOT / "deliverables/Farm_Lugovaya_v1.2.7_Autotests.dt"
    epf = ROOT / ".build/vanessa-tools/single/vanessa-automation-single.epf"
    if not release.is_file() or not epf.is_file() or digest(epf) != EPF_SHA256:
        parser.error("DT 1.2.7 and the pinned Vanessa EPF must be installed first")
    work = ROOT / ".build/vanessa-desktop" / dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    work.mkdir(parents=True, exist_ok=False)
    base = work / "base"
    print(f"Native launcher base: {base}", flush=True)
    designer = ["DESIGNER", "/F", str(base), "/N", "Администратор"]
    for label, flags in [
        ("create", ["CREATEINFOBASE", f"File={base};Locale=ru_RU;"]),
        ("restore", ["DESIGNER", "/F", str(base), "/RestoreIB", str(release)]),
        ("load", [*designer, "/LoadConfigFromFiles", str(ROOT / "configuration")]),
        ("update", [*designer, "/UpdateDBCfg"]),
        ("check", [*designer, "/CheckConfig", "-Server", "-ThinClient", "-ThickClientManagedApplication"]),
    ]:
        code = subprocess.run([str(APP), *flags, "/Out", str(work / f"{label}.log"),
                               "/DisableStartupMessages", "/DisableStartupDialogs"],
                              timeout=180, creationflags=subprocess.CREATE_NO_WINDOW).returncode
        print(f"{label}: {code}", flush=True)
        if code:
            raise RuntimeError(f"{label} failed: {work}")
    python = Path(sys.executable).with_name("pythonw.exe")
    if not python.is_file():
        python = Path(sys.executable)
    settings = {"Python": str(python), "Runner": str(ROOT / "scripts/run_vanessa_tests.py"),
                "Results": str(work / "results")}
    (base / "farm-vanessa-launch.json").write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")
    (work / "result.json").write_text(json.dumps({"base": str(base), "status": "prepared",
        "release": release.name, "release_sha256": digest(release)}, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.open:
        subprocess.Popen([str(APP), "ENTERPRISE", "/F", str(base), "/N", "Администратор",
                          "/DisableStartupMessages", "/DisableStartupDialogs"],
                         creationflags=subprocess.CREATE_NO_WINDOW)


if __name__ == "__main__":
    main()
