"""Download the pinned official Vanessa Single EPF into ignored .build/."""
import io
from pathlib import Path
import urllib.request
import zipfile

from run_vanessa_tests import ROOT, VERSION, EPF_SHA256, digest


def main():
    url = ("https://github.com/Pr-Mex/vanessa-automation/releases/download/"
           f"{VERSION}/vanessa-automation-single.{VERSION}.zip")
    destination = ROOT / ".build/vanessa-tools/single/vanessa-automation-single.epf"
    if destination.is_file() and digest(destination) == EPF_SHA256:
        print(f"Already installed: Vanessa Single {VERSION}")
        return
    with urllib.request.urlopen(url, timeout=120) as response:
        data = response.read()
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        members = [entry for entry in archive.infolist()
                   if Path(entry.filename).name == "vanessa-automation-single.epf"]
        if len(members) != 1:
            raise RuntimeError("Expected exactly one Vanessa Single EPF")
        epf = archive.read(members[0])
    import hashlib
    if hashlib.sha256(epf).hexdigest() != EPF_SHA256:
        raise RuntimeError("Downloaded EPF SHA-256 mismatch; installation cancelled")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(epf)
    print(f"Installed Vanessa Single {VERSION}: {destination}")


if __name__ == "__main__":
    main()
