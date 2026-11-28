"""Configure the native Vanessa button for an existing local file base."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import shutil
import sys

from run_vanessa_tests import APP, EPF_SHA256, ROOT, digest


def configure(base):
    base = base.resolve()
    if not (base / "1Cv8.1CD").is_file():
        raise ValueError("Specify an existing file base containing 1Cv8.1CD")
    runner = ROOT / "scripts/run_vanessa_tests.py"
    epf = ROOT / ".build/vanessa-tools/single/vanessa-automation-single.epf"
    release = ROOT / "deliverables/Farm_Lugovaya_v1.2.7_Autotests.dt"
    for path in (APP, runner, epf, release):
        if not path.is_file():
            raise ValueError(f"Required file missing: {path}")
    if digest(epf) != EPF_SHA256:
        raise ValueError("Installed Vanessa EPF does not match the pinned release")
    python = Path(sys.executable).with_name("pythonw.exe")
    if not python.is_file():
        python = Path(sys.executable)
    key = hashlib.sha256(str(base).casefold().encode("utf-8")).hexdigest()[:16]
    results = ROOT / ".build/vanessa-launchers" / key / "results"
    settings = {"Python": str(python), "Runner": str(runner), "Results": str(results)}
    profile = base / "farm-vanessa-launch.json"
    body = json.dumps(settings, ensure_ascii=False, indent=2)
    if profile.is_file() and profile.read_text(encoding="utf-8-sig") == body:
        return profile
    results.mkdir(parents=True, exist_ok=True)
    if profile.exists():
        stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        shutil.copy2(profile, profile.with_name(profile.name + f".bak-{stamp}"))
    temporary = profile.with_name(profile.name + ".tmp")
    temporary.write_text(body, encoding="utf-8")
    temporary.replace(profile)
    return profile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, type=Path)
    args = parser.parse_args()
    try:
        profile = configure(args.base)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    print(f"Vanessa launcher configured: {profile}")


if __name__ == "__main__":
    main()
