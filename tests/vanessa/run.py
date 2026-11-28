"""Run the farm's Vanessa Automation UI tests in two native 1C sessions."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / ".build" / "vanessa"
FIXTURE = ROOT / "deliverables" / "Farm_Lugovaya_v1.2.5.dt"
FEATURES = Path(__file__).resolve().with_name("features")
VANESSA = WORK / "tools" / "vanessa-automation-single.epf"
VANESSA_SHA256 = "d14080a8b87cebf907109d5acad6424a28dac644d12e13573315a80134f2ed48"

PLATFORM = Path("/Applications/1cv8t.localized/8.3.27.1688")
DESIGNER = PLATFORM / "1cv8t.app/Contents/MacOS/1cv8t"
THIN_CLIENT = PLATFORM / "1cv8ct.app/Contents/MacOS/1cv8ct"
STARTUP_FLAGS = ["/DisableStartupDialogs", "/DisableStartupMessages"]


def _create_base(executable: Path, base: Path, log: Path, template: Path | None = None) -> None:
    args = [str(executable), "CREATEINFOBASE", f'File="{base}";Locale=ru_RU;']
    if template is not None:
        args.extend(["/UseTemplate", str(template)])
    args.extend([*STARTUP_FLAGS, "/Out", str(log)])

    result = subprocess.run(args, check=False, timeout=120)
    if result.returncode or not (base / "1Cv8.1CD").is_file():
        raise RuntimeError(f"1С не создала базу. Журнал {log}")


def _write_params(run_dir: Path, client_base: Path) -> Path:
    reports = run_dir / "junit"
    reports.mkdir()
    profiles = [
        {
            "Имя": user,
            "ПутьКИнфобазе": f'File="{client_base}";',
            "ТипКлиента": "Тонкий",
            "ИмяКомпьютера": "localhost",
            "ПортЗапускаТестКлиента": port,
            "ДопПараметры": f'/N"{user}" /L ru',
        }
        for port, user in enumerate(("Администратор", "Покупка", "Продажа"), start=48150)
    ]
    settings = {
        "projectpath": str(ROOT),
        "featurepath": str(FEATURES),
        "useaddin": False,
        "usethegherkinparserfromthevanessaextaddin": False,
        "runtestclientwithmaximizedwindow": False,
        "OnlyOneTestClientAllowedToRun": True,
        "testclienttimeout": 35,
        "closetestclient": True,
        "stoponerror": True,
        "createlogs": True,
        "logpath": str(run_dir / "status.txt"),
        "junitcreatereport": True,
        "junitpath": str(reports),
        "logtotext": True,
        "logstepstotext": True,
        "textlogname": str(run_dir / "steps.log"),
        "datatestclients": profiles,
    }
    path = run_dir / "VAParams.json"
    path.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8-sig")
    return path


def _run_suite(designer: Path, thin_client: Path, epf: Path, work: Path) -> int:
    run_dir = Path(tempfile.mkdtemp(prefix="run-", dir=work))
    print(f"Каталог прогона {run_dir}", flush=True)

    client_base = run_dir / "farm"
    _create_base(designer, client_base, run_dir / "create-farm.log", FIXTURE)

    manager_base = work / "manager"
    if not (manager_base / "1Cv8.1CD").is_file():
        _create_base(designer, manager_base, run_dir / "create-manager.log")

    params = _write_params(run_dir, client_base)
    options = (
        "StartFeaturePlayer;ShowMainForm;DisableFirstRunHelper;DisableLoadConfig;"
        f"DisableUserSettingsLoader;DisableLoadTestClientsTable;VAParams={params}"
    )
    print("Открываю Vanessa Automation. При первом запуске 1С спросит разрешение открыть EPF.", flush=True)
    with (run_dir / "manager-process.log").open("w", encoding="utf-8") as process_log:
        result = subprocess.run(
            [
                str(thin_client), "ENTERPRISE", "/F", str(manager_base),
                "/L", "ru", "/TestManager", *STARTUP_FLAGS, "/Execute", str(epf),
                "/Out", str(run_dir / "manager.log"), "/C", options,
            ],
            stdout=process_log,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=600,
        )

    status_path = run_dir / "status.txt"
    if not status_path.is_file():
        raise RuntimeError(
            f"Vanessa не записала статус. Код процесса 1С {result.returncode}. Журналы в {run_dir}"
        )
    status = int(status_path.read_text(encoding="utf-8-sig").strip())
    if status == 0 and not any((run_dir / "junit").glob("*.xml")):
        raise RuntimeError(f"Vanessa сообщила об успехе, но не сформировала JUnit. Журналы в {run_dir}")
    print(f"Код Vanessa Automation {status}. Журнал и JUnit в {run_dir}", flush=True)
    return status


def main() -> int:
    """Parse arguments, validate local inputs and run the smoke suite."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epf", type=Path, default=VANESSA, help="Vanessa Automation Single 1.2.043.47")
    parser.add_argument("--designer", type=Path, default=DESIGNER, help="исполняемый файл Конфигуратора")
    parser.add_argument("--thin-client", type=Path, default=THIN_CLIENT, help="исполняемый файл тонкого клиента")
    args = parser.parse_args()

    try:
        for path in (args.epf, args.designer, args.thin_client, FIXTURE):
            if not path.is_file():
                raise RuntimeError(f"Файл не найден {path}")
        with args.epf.open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != VANESSA_SHA256:
                raise RuntimeError("Требуется официальный файл Vanessa Automation Single 1.2.043.47.")
        WORK.mkdir(parents=True, exist_ok=True)
        with (WORK / "run.lock").open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise RuntimeError("Другой прогон Vanessa уже запущен.") from error
            return _run_suite(args.designer.resolve(), args.thin_client.resolve(), args.epf.resolve(), WORK)
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
