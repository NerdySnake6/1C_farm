"""Collect only the successful r2 run and bind evidence to immutable release files."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
E = ROOT/'Документация/04_Тестирование/Протоколы/Итоговая_приемка_1.2.7'
P = E/'Программные_проверки'
P.mkdir(exist_ok=True)
W = ROOT/'.build/final-automated-127-r2'
receipt = json.loads((E/'automated-restore.json').read_text(encoding='utf-8'))
manual_receipt = json.loads((E/'manual-restore.json').read_text(encoding='utf-8'))
release = ROOT/'deliverables/Farm_Lugovaya_v1.2.7_Autotests.dt'
assert receipt['sha256'] == manual_receipt['sha256'] == hashlib.sha256(release.read_bytes()).hexdigest()
counts = {}
for name in ['runtime-tests.txt','form-tests.txt','reservation-tests.txt','reservation-form-tests.txt','schedule-tests.txt','role-Покупка.txt','role-Продажа.txt']:
    source = W/'.build'/name
    body = source.read_text(encoding='utf-8-sig')
    assert not any(line.startswith(('FAIL |','ERROR |')) for line in body.splitlines()), name
    counts[name] = sum(line.startswith('PASS |') for line in body.splitlines())
    shutil.copy2(source, P/name)
    shutil.copy2(source, E/name)
embedded = (W/'embedded-tests.txt').read_text(encoding='utf-8-sig')
assert embedded.count('ПРОЙДЕНО 41 ИЗ 41') == 2 and embedded.rstrip().endswith('COMPLETE')
assert not any(line.startswith(('FAIL |','ERROR |')) for line in embedded.splitlines())
assert 'Посторонняя техническая ошибка отклонена' in embedded
shutil.copy2(W/'embedded-tests.txt',P/'embedded-tests.txt')
shutil.copy2(W/'embedded-tests.txt',E/'embedded-tests.txt')
shutil.copy2(ROOT/'.build/embedded-tests-127/check.txt', P/'Проверка_конфигурации.txt')
hashes = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [release,release.with_suffix('.cf')]}
(E/'SHA256.txt').write_text(''.join(f'{sha}  {name}\n' for name,sha in hashes.items()),encoding='utf-8')
results = json.loads((E/'Ручные/manual-results.json').read_text(encoding='utf-8'))
assert [r['step'] for r in results] == [f'SM{i:02}' for i in range(1,13)]
assert all(r['status']=='PASS' for r in results)
manifest = {'version':'1.2.7','source_run':'final-automated-127-r2','release_sha256':hashes,'standalone_checks':counts,
            'standalone_total':sum(counts.values()),'embedded_runs':[41,41],'manual_steps':12,
            'manual_sequence_note':'Одна восстановленная копия DT, SM01–SM12 по порядку, с паузой по просьбе пользователя внутри SM06. База между шагами не восстанавливалась.',
            'SM10_revision':'Создать новую бронь на20л. Снятую бронь нельзя проводить повторно.',
            'ui_extra':'После SM12 запуск обычной кнопкой41/41, результат сохранён на активной странице; уход в Покупку и возврат сбрасывают статусы.'}
(E/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
lines = ['# Итоговая техническая приёмка версии 1.2.7','','Проверен тот же DT, который приложен к поставке. Контрольные суммы указаны в SHA256.txt.',
         '',manifest['manual_sequence_note'],'','SM10 уточнён до выполнения: после снятия первой брони создаётся новая бронь20л. Повторная активация снятого документа запрещена бизнес-правилом.',
         '',f'Программные наборы: {sum(counts.values())} успешных именованных проверок. Два запуска встроенного набора:41/41 каждый. Эти числа перекрываются, их нельзя складывать как уникальное покрытие.',
         '','## Последовательный ручной прогон','','| Шаг | Роль | Результат |','|---|---|---|']
for r in results:
    evidence = ', '.join(f'[{Path(f).stem}](Ручные/{f})' for f in r['evidence'])
    lines.append(f"| {r['step']} | {r['role']} | **PASS**. {r['result']} {evidence} |")
lines += ['','## Проверка встроенного экрана после SM12','',
          '[План проверок](Ручные/UI127-plan.jpg), [41 из41](Ручные/UI127-results.jpg), [сброс при возвращении](Ручные/UI127-reset-after-leave.jpg).',
          '','На активной странице результат41/41 сохранился. После перехода в Покупку и возврата все строки вновь НЕ ЗАПУЩЕН. Жёлтая панель сообщений об ожидаемых отказах не появилась.',
          '','## Исправление ложного успеха','',
          'Негативные проверки извлекают конечную причину исключения и сравнивают с ожидаемым сообщением правила. Контрольная посторонняя ошибка «Метод объекта не обнаружен (Записать)» отклонена помощником, это зафиксировано в embedded-tests.txt.',
          '','При проверке найден старый дефект фикстуры T18: документ создавался в откатываемой транзакции и терял ссылку. Фикстура исправлена. Теперь T18 получает именно нехватку1л при суммарном превышении остатка повторяющимися строками.',
          '','## Границы заключения','',
          'Закрыты три оставшихся технических замечания: отсутствие итогового последовательного прогона, рассогласованные версии актуальных материалов, ложный успех при постороннем исключении. Это технический протокол, а не подпись заказчика под актом приёмки. Нагрузка, конкурентные продажи и процент покрытия кода не проверялись.', '']
(E/'Протокол.md').write_text('\n'.join(lines),encoding='utf-8')
print(json.dumps(manifest,ensure_ascii=False,indent=2))
