"""Run the 41 built-in 1C checks on a fresh copy of release 1.2.5.

Usage: python scripts/run_defense_tests.py
No external Python packages required. Evidence stays in documentation.
"""
import argparse
from collections import Counter
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_APP = Path(r'C:\Program Files (x86)\1cv8t\8.3.27.1688\bin\1cv8t.exe')
EXPECTED = {
    'reservation-tests.txt': {f'B{i:02}' for i in range(1, 33)},
    'reservation-form-tests.txt': {f'BF{i:02}' for i in range(1, 10)},
}


def validate_report(body, expected):
    """Require each expected assertion once and reject incomplete/error reports."""
    lines = [line.strip() for line in body.lstrip('\ufeff').splitlines() if line.strip()]
    ids = []
    for line in lines:
        if line == 'COMPLETE':
            continue
        match = re.fullmatch(r'PASS \| (B(?:F)?\d{2}) .+', line)
        if not match:
            raise ValueError(f'Unexpected or failed report line: {line}')
        ids.append(match.group(1))
    if not lines or lines[-1] != 'COMPLETE' or lines.count('COMPLETE') != 1:
        raise ValueError('Report must end with exactly one COMPLETE')
    counts = Counter(ids)
    missing, extra = expected - counts.keys(), counts.keys() - expected
    duplicates = sorted(key for key, count in counts.items() if count != 1)
    if missing or extra or duplicates:
        raise ValueError(f'missing={sorted(missing)}, extra={sorted(extra)}, duplicates={duplicates}')
    return {'passed': len(ids), 'ids': sorted(ids), 'complete': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app', type=Path, default=DEFAULT_APP, help='Path to 1cv8t.exe')
    args = parser.parse_args()
    release = ROOT / 'deliverables/Farm_Lugovaya_v1.2.5.dt'
    for required in (args.app, release):
        if not required.is_file():
            parser.error(f'File not found: {required}')
    stamp = dt.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    work = ROOT / '.build' / f'defense-tests-{stamp}'
    evidence = ROOT / 'Документация/04_Тестирование/Защита_21_ноября/Протоколы' / stamp
    work.mkdir(parents=True)
    evidence.mkdir(parents=True)
    (work / '.build').mkdir()
    base = work / 'base'
    summary = {'started': dt.datetime.now().astimezone().isoformat(),
               'release': release.name, 'release_sha256': hashlib.sha256(release.read_bytes()).hexdigest(),
               'platform': str(args.app), 'work': str(work), 'status': 'INCOMPLETE',
               'steps': [], 'reports': []}
    steps = [
        ('create', ['CREATEINFOBASE', f'File={base};Locale=ru_RU;']),
        ('restore', ['DESIGNER', '/F', str(base), '/RestoreIB', str(release)]),
        ('reservations', ['ENTERPRISE', '/F', str(base), '/N', 'Администратор',
                          '/C', f'FarmReservationTests={work}']),
    ]
    try:
        shutil.copytree(ROOT / 'assets', work / 'assets')
        for name, command in steps:
            print(f'Running {name}...', flush=True)
            result = subprocess.run([str(args.app), *command, '/Out', str(evidence / f'{name}.log'),
                                     '/DisableStartupMessages', '/DisableStartupDialogs'],
                                    timeout=180, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            summary['steps'].append({'step': name, 'exit_code': result.returncode})
            if result.returncode:
                raise RuntimeError(f'{name}: exit code {result.returncode}')
        for filename, expected in EXPECTED.items():
            report = validate_report((work / '.build' / filename).read_text(encoding='utf-8-sig'), expected)
            summary['reports'].append({'file': filename, **report})
            print(f'{filename}: {report["passed"]} PASS, COMPLETE', flush=True)
        summary['status'] = 'PASS'
    except Exception as exc:
        summary.update(status='FAILED', error=str(exc))
        print(f'FAILED: {exc}', flush=True)
    finally:
        for filename in EXPECTED:
            source = work / '.build' / filename
            if source.is_file():
                shutil.copy2(source, evidence / filename)
        summary['finished'] = dt.datetime.now().astimezone().isoformat()
        (evidence / 'result.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'{summary["status"]}: {evidence / "result.json"}', flush=True)
    return 0 if summary['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
