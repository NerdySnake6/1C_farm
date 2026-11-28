"""Package the defense and everything needed for a fresh 1C test run."""
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Документация/04_Тестирование/Защита_21_ноября'
deck = OUT / 'Автотесты_Луговая_защита.pptx'
with zipfile.ZipFile(deck) as pptx:
    ns = {'p': 'http://schemas.openxmlformats.org/presentationml/2006/main'}
    slides = ET.fromstring(pptx.read('ppt/presentation.xml')).find('p:sldIdLst', ns)
    assert len(slides) == 8
    assert all(f'ppt/notesSlides/notesSlide{i}.xml' in pptx.namelist() for i in range(1, 9))
files = [
    ROOT / 'scripts/run_defense_tests.py',
    ROOT / 'scripts/test_defense_runner.py',
    ROOT / 'scripts/build_defense_notes.py',
    ROOT / 'scripts/defense_slides.json',
    ROOT / 'deliverables/Farm_Lugovaya_v1.2.5.dt',
    ROOT / 'configuration/CommonModules/СервисФермы/Ext/Module.bsl',
    ROOT / 'configuration/Ext/ManagedApplicationModule.bsl',
    *(ROOT / 'assets' / name for name in ['milk.png', 'curd.png', 'cream.png']),
    *(file for file in OUT.rglob('*') if file.is_file() and file.suffix not in ('.zip', '.log')),
]
archive = OUT / 'Автотесты_и_защита.zip'
with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as package:
    for file in files:
        package.write(file, file.relative_to(ROOT).as_posix())
    package.writestr('ЗАПУСК.txt',
        '1. Распакуйте архив целиком.\n'
        '2. Нужны Python 3.9+ и учебная 1С 8.3.27.1688.\n'
        '3. Откройте терминал в папке, где находятся scripts, assets и deliverables.\n'
        '4. Выполните: python scripts/run_defense_tests.py\n'
        'Другой путь платформы: python scripts/run_defense_tests.py --app "C:\\путь\\1cv8t.exe"\n'
        'Новая база создается автоматически. Нужны свободное место и право записи в распакованную папку.\n'
        '5. Презентация, речь и протоколы находятся в Документация/04_Тестирование/Защита_21_ноября.\n'
        '6. Проверка оболочки: python scripts/test_defense_runner.py\n')
print(f'{archive} ({archive.stat().st_size:,} bytes)')
