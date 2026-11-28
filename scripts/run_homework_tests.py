"""Run existing 1C reservation tests in a NEW isolated copy of release 1.2.5.

Windows: python scripts/run_homework_tests.py
Requires the locally installed educational 1C platform. Never uses a working DB.
"""
from pathlib import Path
import datetime
import json
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
APP = Path(r'C:\Program Files (x86)\1cv8t\8.3.27.1688\bin\1cv8t.exe')


def main():
    if not APP.is_file():
        raise SystemExit(f'1C executable not found: {APP}')
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    work = ROOT / '.build' / f'homework-tests-{stamp}'
    work.mkdir(parents=True)
    base = work / 'base'
    logs = work / '.build'
    logs.mkdir()
    shutil.copytree(ROOT / 'assets', work / 'assets')
    release = ROOT / 'deliverables' / 'Farm_Lugovaya_v1.2.5.dt'
    steps = [
        ('create', ['CREATEINFOBASE', f'File={base};Locale=ru_RU;']),
        ('restore', ['DESIGNER', '/F', str(base), '/RestoreIB', str(release)]),
        ('reservations', ['ENTERPRISE', '/F', str(base), '/N', 'Администратор',
                          '/C', f'FarmReservationTests={work}']),
    ]
    summary = {'started': datetime.datetime.now().astimezone().isoformat(),
               'release': str(release), 'work': str(work), 'steps': [], 'status': 'INCOMPLETE'}
    try:
        for name, args in steps:
            print(f'Running {name}...', flush=True)
            log = work / f'{name}.log'
            result = subprocess.run([str(APP), *args, '/Out', str(log),
                                     '/DisableStartupMessages', '/DisableStartupDialogs'],
                                    timeout=180, creationflags=subprocess.CREATE_NO_WINDOW)
            summary['steps'].append({'step': name, 'exit_code': result.returncode})
            if result.returncode:
                raise RuntimeError(f'{name}: exit code {result.returncode}. See {log}')
        reports = []
        for filename in ['reservation-tests.txt', 'reservation-form-tests.txt']:
            file = logs / filename
            body = file.read_text(encoding='utf-8-sig')
            passed = sum(line.startswith('PASS |') for line in body.splitlines())
            complete = 'COMPLETE' in body.splitlines() and 'ERROR |' not in body
            reports.append({'file': filename, 'pass': passed, 'complete': complete})
            print(f'{filename}: {passed} PASS, complete={complete}', flush=True)
            if not complete or passed == 0:
                raise RuntimeError(f'Failed report: {file}')
        summary['reports'] = reports
        summary['status'] = 'PASS'
    except Exception as exc:
        summary['status'] = 'FAILED'
        summary['error'] = str(exc)
        print(str(exc), file=sys.stderr)
    finally:
        summary['finished'] = datetime.datetime.now().astimezone().isoformat()
        (work / 'result.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'Result: {work / "result.json"}', flush=True)
    return 0 if summary['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
