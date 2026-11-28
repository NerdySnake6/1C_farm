"""Run Vanessa Single against a NEW disposable 1.2.7 base; never accept a live base."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
VERSION = "1.2.043.45"
EPF_SHA256 = "4173a2a2b3690d05a2261015e09bc7837b0904cf1493ce2c28c56431e8dfb9fa"
APP = Path(r"C:\Program Files (x86)\1cv8t\8.3.27.1688\bin\1cv8t.exe")


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def scenario_results(directory):
    """Keep per-case evidence even when the suite fails validation."""
    results = []
    for path in sorted(directory.glob("*.xml")):
        for case in ET.parse(path).getroot().iter("testcase"):
            status, detail = "passed", ""
            for tag in ("failure", "error", "skipped"):
                node = case.find(tag)
                if node is not None:
                    status = "skipped" if tag == "skipped" else "failed"
                    detail = "\n".join(filter(None, (node.get("message", ""), node.text or ""))).strip()
                    break
            name = case.get("name", "")
            results.append({"code": name.split(" ", 1)[0], "name": name,
                            "status": status, "duration": case.get("time", ""),
                            "detail": detail[:12000]})
    return results


def validate_reports(directory, expected=3):
    cases = []
    for path in directory.glob("*.xml"):
        cases.extend(ET.parse(path).getroot().iter("testcase"))
    if len(cases) != expected:
        raise RuntimeError(f"Expected {expected} JUnit cases, got {len(cases)}")
    if len({case.get('name') for case in cases}) != expected:
        raise RuntimeError("Duplicate JUnit cases")
    for case in cases:
        if any(case.find(tag) is not None for tag in ("failure", "error", "skipped")):
            raise RuntimeError(f"Unsuccessful scenario: {case.get('name')}")
    return [case.get("name") for case in cases]


def close_test_clients(base):
    """Close only thin clients whose /F argument is this disposable base."""
    if os.name != "nt":
        return
    command = """
$ErrorActionPreference = 'Stop'
$baseArgument = '/F"' + $env:FARM_VANESSA_BASE + '"'
Get-CimInstance Win32_Process -Filter "Name='1cv8ct.exe'" |
    Where-Object { $_.CommandLine -and $_.CommandLine.Contains($baseArgument) } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -ErrorAction SilentlyContinue }
"""
    subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
                   env={**os.environ, "FARM_VANESSA_BASE": str(base)}, check=True, timeout=90,
                   capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", type=Path, default=APP)
    parser.add_argument("--epf", type=Path, default=ROOT / ".build/vanessa-tools/single/vanessa-automation-single.epf")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--ui-result", type=Path, help="Write progress for the native 1C launcher inside .build")
    args = parser.parse_args()
    if args.ui_result:
        args.ui_result = args.ui_result.resolve()
        if not args.ui_result.is_relative_to((ROOT / ".build").resolve()):
            parser.error("UI result must be inside this repository's .build directory")

    def fail_preflight(message):
        if args.ui_result:
            args.ui_result.parent.mkdir(parents=True, exist_ok=True)
            args.ui_result.write_text(json.dumps({"status": "failed", "error": message}, ensure_ascii=False), encoding="utf-8")
        parser.error(message)

    release = ROOT / "deliverables/Farm_Lugovaya_v1.2.7_Autotests.dt"
    for path in (args.app, args.epf, release):
        if not path.is_file():
            fail_preflight(f"Required file missing: {path}")
    if digest(args.epf) != EPF_SHA256:
        fail_preflight(f"EPF must be Vanessa Single {VERSION}, SHA-256 mismatch")
    work = ROOT / ".build/vanessa-runs" / dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    work.mkdir(parents=True, exist_ok=False)
    base = work / "base"
    manager = work / "manager"
    reports = work / "junit"
    reports.mkdir()
    features = work / "features"
    shutil.copytree(ROOT / "tests/vanessa/features", features)
    listeners = [socket.socket() for _ in range(3)]
    try:
        for listener in listeners:
            listener.bind(("127.0.0.1", 0))
        client_ports = [listener.getsockname()[1] for listener in listeners]
    finally:
        for listener in listeners:
            listener.close()
    shutil.copytree(ROOT / "assets", work / "assets", ignore=shutil.ignore_patterns("test-defense", "project-management"))
    receipt = {"vanessa": VERSION, "epf_sha256": digest(args.epf), "release": release.name,
               "release_sha256": digest(release), "base": str(base),
               "source": "DT 1.2.7 + current configuration/", "status": "preparing"}
    source_hash = hashlib.sha256()
    for source in sorted((ROOT / "configuration").rglob("*")):
        if source.is_file():
            source_hash.update(source.relative_to(ROOT).as_posix().encode("utf-8") + b"\0")
            source_hash.update(bytes.fromhex(digest(source)))
    receipt["configuration_sha256"] = source_hash.hexdigest()
    receipt["feature_sha256"] = digest(features / "embedded_checks.feature")
    receipt["features_sha256"] = {
        path.name: digest(path) for path in sorted(features.glob("*.feature"))
    }

    def save():
        body = json.dumps(receipt, ensure_ascii=False, indent=2)
        (work / "result.json").write_text(body, encoding="utf-8")
        if args.ui_result:
            args.ui_result.parent.mkdir(parents=True, exist_ok=True)
            temporary = args.ui_result.with_suffix(".tmp")
            temporary.write_text(body, encoding="utf-8")
            temporary.replace(args.ui_result)

    def run(label, parameters, timeout=180):
        print(label, flush=True)
        process = subprocess.Popen([str(args.app.resolve()), *parameters, "/Out", str(work / f"{label}.log"),
                                    "/DisableStartupMessages", "/DisableStartupDialogs"],
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            # Stop only the process tree created by this invocation, never other 1C sessions.
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                               capture_output=True, timeout=30,
                               creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                process.kill()
            process.wait(timeout=30)
            raise RuntimeError(f"{label}: timeout after {timeout}s; see {work}") from None
        if code:
            raise RuntimeError(f"{label}: exit {code}; see {work}")

    save()
    print(f"Disposable base and evidence: {work}", flush=True)
    fixtures_attempted = False
    try:
        run("create", ["CREATEINFOBASE", f'File={base};Locale=ru_RU;'])
        run("restore", ["DESIGNER", "/F", str(base), "/RestoreIB", str(release)])
        designer = ["DESIGNER", "/F", str(base), "/N", "Администратор"]
        run("load", [*designer, "/LoadConfigFromFiles", str(ROOT / "configuration")])
        run("update", [*designer, "/UpdateDBCfg"])
        run("check", [*designer, "/CheckConfig", "-Server", "-ThinClient", "-ThickClientManagedApplication"])
        (work / "vanessa-test-base.json").write_text(json.dumps({
            "kind": "farm-vanessa-disposable-v1", "base": str(base)
        }), encoding="utf-8")
        run("users", ["ENTERPRISE", "/F", str(base), "/N", "Администратор", "/C", "FarmUsers"])
        fixtures_attempted = True
        run("fixtures", ["ENTERPRISE", "/F", str(base), "/N", "Администратор",
                         "/C", f"FarmVanessaPrepare={work}"])
        if (work / "fixture-error.txt").exists():
            raise RuntimeError((work / "fixture-error.txt").read_text(encoding="utf-8-sig"))
        variables = json.loads((work / "fixtures.json").read_text(encoding="utf-8-sig"))
        run("create-manager", ["CREATEINFOBASE", f'File={manager};Locale=ru_RU;'])
        settings = {
            "GlobalVars": variables,
            "ТаймаутЗапуска1С": 90,
            "КаталогФич": str(features),
            "КаталогПроекта": str(ROOT), "ВыполнитьСценарии": True,
            "ЗавершитьРаботуСистемы": True, "ЗакрыватьКлиентТестированияПринудительно": True,
            "ИспользоватьКомпонентуVanessaExt": False,
            "ИспользоватьПарсерGherkinИзКомпонентыVanessaExt": False,
            "ДелатьОтчетВФорматеjUnit": True, "КаталогВыгрузкиJUnit": str(reports),
            "ВыгружатьСтатусВыполненияСценариевВФайл": True,
            "ПутьКФайлуДляВыгрузкиСтатусаВыполненияСценариев": str(work / "status.txt"),
            "ДанныеКлиентовТестирования": [
                {"Имя": name, "ТипКлиента": "Тонкий", "ПутьКИнфобазе": f'File="{base}";',
                 "ИмяКомпьютера": "localhost", "ПортЗапускаТестКлиента": port,
                 "ДопПараметры": f'/N"{user}" /Lru /VLru'}
                for name, user, port in zip(
                    ("ФермаVanessa", "ФермаПокупка", "ФермаПродажа"),
                    ("Администратор", "Покупка", "Продажа"), client_ports)],
            "ПриравниватьPendingКFailed": True,
            "СобиратьДанныеОСостоянииАктивнойФормыПриОшибке": True,
        }
        params = work / "VAParams.json"
        params.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8-sig")
        receipt["status"] = "running"
        save()
        run("vanessa", ["ENTERPRISE", "/F", str(manager), "/TESTMANAGER",
                        "/Execute", str(args.epf.resolve()), "/C",
                        f"StartFeaturePlayer;VAParams={params};DisableFirstRunHelper;DisableLoadConfig;DisableLoadTestClientsTable"], args.timeout)
        if (work / "status.txt").read_text(encoding="utf-8-sig").strip() != "0":
            raise RuntimeError(f"Vanessa status is not zero; see {work}")
        receipt["scenarios"] = validate_reports(reports, expected=18)
        receipt["status"] = "passed"
    except Exception as error:
        receipt["status"] = "failed"
        receipt["error"] = str(error)
        raise
    finally:
        try:
            receipt["scenario_results"] = scenario_results(reports)
        except Exception as error:
            receipt["report_error"] = str(error)
            receipt["status"] = "failed"
        try:
            close_test_clients(base)
            if fixtures_attempted and (base / "farm-vanessa-fixtures.bin").is_file():
                run("cleanup", ["ENTERPRISE", "/F", str(base), "/N", "Администратор",
                                "/C", f"FarmVanessaCleanup={work}"])
                if (work / "cleanup.txt").read_text(encoding="utf-8-sig").strip() != "CLEAN":
                    raise RuntimeError("Fixture cleanup did not confirm the original data snapshot")
                receipt["cleanup"] = "original snapshot restored"
        except Exception as error:
            receipt["status"] = "failed"
            receipt["cleanup_error"] = str(error)
            save()
            raise
        save()
    print("PASS: 18 Vanessa scenarios; fixture cleanup verified", flush=True)


if __name__ == "__main__":
    main()
