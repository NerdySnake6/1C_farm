"""Prepare separate bases from the exact 1.2.7 DT and run release checks."""
from pathlib import Path
import datetime
import hashlib
import json
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
APP = Path(r'C:\Program Files (x86)\1cv8t\8.3.27.1688\bin\1cv8t.exe')
RELEASE = ROOT / 'deliverables/Farm_Lugovaya_v1.2.7_Autotests.dt'
EVIDENCE = ROOT / 'Документация/04_Тестирование/Протоколы/Итоговая_приемка_1.2.7'
EVIDENCE.mkdir(parents=True, exist_ok=True)
RUN_LABEL = '127-r2'

def run(label, args, timeout=180):
    log = EVIDENCE / f'{label}.log'
    result = subprocess.run([str(APP), *args, '/Out', str(log), '/DisableStartupMessages', '/DisableStartupDialogs'],
                            timeout=timeout, creationflags=subprocess.CREATE_NO_WINDOW)
    print(f'{label}: {result.returncode}', flush=True)
    if result.returncode:
        raise RuntimeError(log.read_text(encoding='utf-8-sig'))

def restore(name):
    work = ROOT / '.build' / f'final-{name}-{RUN_LABEL}'
    if (work / 'base/1Cv8.1CD').exists():
        raise RuntimeError(f'Refusing to overwrite existing acceptance base: {work}')
    (work / '.build').mkdir(parents=True, exist_ok=True)
    (work / 'assets').mkdir(exist_ok=True)
    for file in ['milk.png', 'curd.png', 'cream.png']:
        shutil.copy2(ROOT/'assets'/file, work/'assets'/file)
    run(f'{name}-create', ['CREATEINFOBASE', f'File={work / "base"};Locale=ru_RU;'])
    run(f'{name}-restore', ['DESIGNER', '/F', str(work/'base'), '/RestoreIB', str(RELEASE)])
    receipt = {'release': RELEASE.name, 'sha256': hashlib.sha256(RELEASE.read_bytes()).hexdigest(),
               'restored_at': datetime.datetime.now().astimezone().isoformat(), 'base': str(work/'base')}
    (EVIDENCE / f'{name}-restore.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
    return work

action = sys.argv[1]
if action == 'prepare-manual':
    work = restore('manual')
    print(work, flush=True)
elif action == 'automated':
    work = restore('automated')
    for parameter in ('FarmTests', 'FarmReservationTests', 'FarmEmbeddedTests', 'FarmScheduleTests'):
        run(parameter, ['ENTERPRISE', '/F', str(work/'base'), '/N', 'Администратор', '/C', f'{parameter}={work}'])
        if parameter == 'FarmEmbeddedTests':
            shutil.copy2(work/'embedded-tests.txt', EVIDENCE/'embedded-tests.txt')
        for file in (work/'.build').glob('*.txt'):
            shutil.copy2(file, EVIDENCE/file.name)
        for file in (work/'.build').glob('*.txt'):
            body = file.read_text(encoding='utf-8-sig')
            if 'ERROR |' in body or any(line.startswith('FAIL |') for line in body.splitlines()):
                raise RuntimeError(f'Failed report: {file}')
    for user in ('Покупка', 'Продажа'):
        run('role-'+user, ['ENTERPRISE', '/F', str(work/'base'), '/N', user, '/C', f'FarmRole={work}'])
        shutil.copy2(work/'.build'/f'role-{user}.txt', EVIDENCE/f'role-{user}.txt')
    for file in EVIDENCE.glob('*.txt'):
        if file.name.startswith('SHA'):
            continue
        body = file.read_text(encoding='utf-8-sig')
        if 'ERROR |' in body:
            raise RuntimeError(f'Failed report: {file}')
    print('Automated release checks complete', flush=True)
elif action == 'launch-manual':
    base = ROOT/'.build'/f'final-manual-{RUN_LABEL}'/'base'
    assert (base/'1Cv8.1CD').is_file()
    user = sys.argv[2] if len(sys.argv)>2 else 'Администратор'
    subprocess.Popen([str(APP), 'ENTERPRISE', '/F', str(base), '/N', user,
                      '/DisableStartupMessages', '/DisableStartupDialogs'])
else:
    raise SystemExit('Use automated, prepare-manual or launch-manual [user]')
