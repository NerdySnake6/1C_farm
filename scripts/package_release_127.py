"""Package only current release artifacts and evidence cited by the acceptance protocol."""
from pathlib import Path
import hashlib
import json
import re
import zipfile
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'Документация/04_Тестирование/Протоколы/Итоговая_приемка_1.2.7'
D=ROOT/'Документация/Актуальная_поставка_1.2.7'
F=ROOT/'Документация/04_Тестирование/Защита_21_ноября'
manifest=json.loads((E/'manifest.json').read_text(encoding='utf-8'))
manual=json.loads((E/'Ручные/manual-results.json').read_text(encoding='utf-8'))
closure='''# Закрытие оставшихся технических замечаний 1.2.7

Статус трёх замечаний: **закрыты**.

| Замечание | Что изменено | Подтверждение |
|---|---|---|
| Ложный успех при любом исключении | Проверка конечной причины отказа, отдельная защита от посторонней ошибки, исправленная фикстура T18 | embedded-tests.txt и runtime-tests.txt |
| Нет итогового последовательного SM01–SM12 | 12 шагов выполнены по порядку в одной копии итогового DT, с пользовательской паузой внутри SM06 и продолжением с того же документа | Итоговый протокол, снимки и manual-results.json |
| Разные версии актуальных материалов | Текущая поставка, инструкция, отчёт, презентация и речь согласованы на 1.2.7 | README, SHA256.txt, документы актуальной поставки |

Программные наборы дали94 успешные проверки, два запуска встроенных тестов —41/41 каждый. Дополнительный запуск обычной кнопкой после ручных шагов также дал41/41. Наборы перекрываются, эти числа не складываются в уникальное покрытие.

[Первичные доказательства](../04_Тестирование/Протоколы/Итоговая_приемка_1.2.7/Протокол.md).

[Оформленный документ закрытия](../Актуальная_поставка_1.2.7/Закрытие_замечаний_1.2.7.docx).

Техническое закрытие относится к перечисленным трём оставшимся замечаниям. Документы прежних выпусков сохранены как история. Нагрузка и конкурентные продажи не проверялись. Этот документ не заменяет подпись заказчика под актом.
'''.replace('дали94','дали 94').replace('—41/41','— 41/41').replace('дал41/41','дал 41/41')
C=ROOT/'Документация/08_Ответ_на_претензию/Закрытие_оставшихся_замечаний_1.2.7.md'
C.write_text(closure,encoding='utf-8')
files=[ROOT/'README.md',C,*[p for p in D.glob('*.docx') if not p.name.startswith('~$')],F/'Автотесты_Луговая_защита_1.2.7.pptx',F/'Текст_защиты_автотесты.md',
       E/'Протокол.md',E/'manifest.json',E/'SHA256.txt',E/'automated-restore.json',E/'manual-restore.json',E/'Ручные/manual-results.json',
       E/'Ручные/ui-events.jsonl',*list((E/'Программные_проверки').glob('*'))]
for r in manual:
    files.extend(E/'Ручные'/name for name in r['evidence'])
files.extend(E/'Ручные'/name for name in ['UI127-home.jpg','UI127-plan.jpg','UI127-results.jpg','UI127-reset-after-leave.jpg'])
for extension in ['dt','cf']:
    f=ROOT/f'deliverables/Farm_Lugovaya_v1.2.7_Autotests.{extension}'
    assert hashlib.sha256(f.read_bytes()).hexdigest()==manifest['release_sha256'][f.name]
    files.append(f)
files.extend(p for p in (ROOT/'configuration').rglob('*') if p.is_file())
files.extend(ROOT/'scripts'/name for name in ['build_embedded_release.py','wire_embedded_tests.py','harden_refusal_checks.py','final_acceptance.py','collect_final_release.py','build_current_docs_127.py','package_release_127.py','build_embedded_defense_notes.py','defense_slides_v2.json'])
files.extend((ROOT/'scripts/bsl').glob('ВстроенныеАвтотесты*.bsl'))
files=list(dict.fromkeys(files))
assert all(f.is_file() for f in files)
sha_lines=''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(ROOT).as_posix()}\n' for p in files)
(D/'Состав_комплекта_SHA256.txt').write_text(sha_lines,encoding='utf-8')
files.append(D/'Состав_комплекта_SHA256.txt')
archive=ROOT/'deliverables/Ферма_Луговая_1.2.7_итог.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for f in files:z.write(f,f.relative_to(ROOT).as_posix())
    z.writestr('НАЧНИТЕ_ЗДЕСЬ.txt','Поставка1.2.7. Инструкция и ссылки находятся в README.md.\nВосстановите DT в отдельную пустую файловую базу.\nВойдите как Администратор и нажмите Автотесты → Запустить41 проверку.\nПрезентация и речь находятся в Документация/04_Тестирование/Защита_21_ноября.\nДокумент закрытия трёх оставшихся замечаний находится в Документация/Актуальная_поставка_1.2.7.\n')
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
print(archive)
print('Files:',len(files),'Bytes:',archive.stat().st_size)
