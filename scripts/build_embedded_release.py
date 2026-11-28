"""Build and check the embedded-test release using a fresh isolated base."""
from pathlib import Path
import datetime
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
APP = Path(r'C:\Program Files (x86)\1cv8t\8.3.27.1688\bin\1cv8t.exe')
WORK = ROOT / '.build/embedded-tests-127'
BASE = WORK / 'base'
WORK.mkdir(parents=True, exist_ok=True)

def run(name, args):
    log = WORK / f'{name}.txt'
    result = subprocess.run([str(APP), *args, '/Out', str(log), '/DisableStartupMessages', '/DisableStartupDialogs'],
                            timeout=180, creationflags=subprocess.CREATE_NO_WINDOW)
    print(f'{name}: exit {result.returncode}', flush=True)
    if result.returncode:
        if log.exists():
            print(log.read_text(encoding='utf-8-sig'), flush=True)
        raise SystemExit(result.returncode)

action = sys.argv[1] if len(sys.argv) > 1 else 'build'
designer = ['DESIGNER', '/F', str(BASE), '/N', 'Администратор']
if action == 'build':
    if not (BASE / '1Cv8.1CD').exists():
        run('create', ['CREATEINFOBASE', f'File={BASE};Locale=ru_RU;'])
        run('restore', ['DESIGNER', '/F', str(BASE), '/RestoreIB', str(ROOT/'deliverables/Farm_Lugovaya_v1.2.5.dt')])
    run('load', [*designer, '/LoadConfigFromFiles', str(ROOT/'configuration')])
    run('update', [*designer, '/UpdateDBCfg'])
    run('check', [*designer, '/CheckConfig', '-Server', '-ThinClient', '-ThickClientManagedApplication'])
elif action == 'test':
    run('embedded', ['ENTERPRISE', '/F', str(BASE), '/N', 'Администратор', '/C', 'FarmEmbeddedTests=' + str(WORK)])
    report = (WORK / 'embedded-tests.txt').read_text(encoding='utf-8-sig')
    print(report, flush=True)
    if 'ERROR |' in report or report.count('ПРОЙДЕНО 41 ИЗ 41') != 2 or not report.rstrip().endswith('COMPLETE'):
        raise SystemExit('Embedded test verification failed')
elif action == 'export':
    for extension, flag in [('dt', '/DumpIB'), ('cf', '/DumpCfg')]:
        run('export-' + extension, [*designer, flag, str(ROOT / f'deliverables/Farm_Lugovaya_v1.2.7_Autotests.{extension}')])
else:
    raise SystemExit('Use build, test or export')
