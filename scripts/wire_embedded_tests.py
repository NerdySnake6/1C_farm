"""Wire the built-in test screen into configuration sources (idempotent)."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CONF = ROOT / 'configuration'
FORM_ID = '2e9bac04-3899-4b80-afc1-4cb20a507829'
service = CONF / 'CommonModules/СервисФермы/Ext/Module.bsl'
body = service.read_text(encoding='utf-8-sig')
marker = '// Автотесты используют собственные объекты'
body = body.split(marker)[0].rstrip() + '\n\n'
service.write_text(body + (ROOT / 'scripts/bsl/ВстроенныеАвтотестыСервер.bsl').read_text(encoding='utf-8') + '\n' + (ROOT / 'scripts/bsl/ПрямыеСценарииVanessa.bsl').read_text(encoding='utf-8'), encoding='utf-8-sig')

app_file = CONF / 'Ext/ManagedApplicationModule.bsl'
app = app_file.read_text(encoding='utf-8-sig')
start = app.index('            СсылкаБрони = СервисФермы.ПодготовитьПроверкуФормыБрони')
end = start + re.search(r'^        Исключение\r?$', app[start:], re.M).start()
checks = app[start:end]
checks = checks.replace('СервисФермы.ПодготовитьПроверкуФормыБрони(Сред(ПараметрЗапуска, 22))', 'СервисФермы.БроньВстроенногоТеста(Запуск)')
checks = checks.replace('ПротоколБрони.ЗаписатьСтроку(', 'Протокол.Добавить(')
form_body = (ROOT / 'scripts/bsl/ВстроенныеАвтотестыФорма.bsl').read_text(encoding='utf-8')
form_body += '\n&НаКлиенте\nПроцедура ВыполнитьПроверкиФорм(Запуск, Протокол)\n    ФормаБрони = Неопределено;\n    Попытка\n'
form_body += checks
form_body += '''    Исключение
        Протокол.Добавить("ERROR | " + ОписаниеОшибки());
    КонецПопытки;
    Для Каждого СсылкаПродажи Из СервисФермы.ПродажиВстроенногоТеста(Запуск) Цикл
        Попытка
            ФормаПродажи = ПолучитьФорму("Документ.Расход.ФормаОбъекта", Новый Структура("Ключ", СсылкаПродажи));
            ФормаПродажи.Закрыть();
        Исключение
            Протокол.Добавить("ERROR | Закрытие продажи: " + ОписаниеОшибки());
        КонецПопытки;
    КонецЦикла;
    Если ФормаБрони <> Неопределено Тогда
        Попытка ФормаБрони.Закрыть(); Исключение Протокол.Добавить("ERROR | Закрытие формы: " + ОписаниеОшибки()); КонецПопытки;
    КонецЕсли;
КонецПроцедуры
'''
form_dir = CONF / 'CommonForms/Автотесты/Ext'
(form_dir / 'Form').mkdir(parents=True, exist_ok=True)
(form_dir / 'Form/Module.bsl').write_text(form_body, encoding='utf-8-sig')
metadata = (CONF / 'CommonForms/РабочийСтол.xml').read_text(encoding='utf-8-sig')
metadata = metadata.replace('e223b2b6-4c7a-58eb-a7ae-a2dc1c867cd2', FORM_ID).replace('РабочийСтол', 'Автотесты').replace('Рабочий стол фермы', 'Автоматические проверки')
(CONF / 'CommonForms/Автотесты.xml').write_text(metadata, encoding='utf-8-sig')
xml = (CONF / 'CommonForms/РабочийСтол/Ext/Form.xml').read_text(encoding='utf-8-sig')
xml = xml.replace('</Events>', '''    <Event name="OnOpen">ПриОткрытии</Event>
    <Event name="BeforeClose">ПередЗакрытием</Event>
    <Event name="OnClose">ПриЗакрытии</Event>
    </Events>''')
xml = xml.replace('<Attributes/>', '''<Attributes>
    <Attribute name="Результат" id="10"><Type><v8:Type xmlns:mxl="http://v8.1c.ru/8.2/data/spreadsheet">mxl:SpreadsheetDocument</v8:Type></Type></Attribute>
    <Attribute name="РезультатVanessa" id="14"><Type><v8:Type xmlns:mxl="http://v8.1c.ru/8.2/data/spreadsheet">mxl:SpreadsheetDocument</v8:Type></Type></Attribute>
    <Attribute name="ТекстПротокола" id="11"><Type><v8:Type>xs:string</v8:Type></Type></Attribute>
    <Attribute name="Успешно" id="12"><Type><v8:Type>xs:boolean</v8:Type></Type></Attribute>
    <Attribute name="Пройдено" id="13"><Type><v8:Type>xs:decimal</v8:Type></Type></Attribute>
    </Attributes>''')
(form_dir / 'Form.xml').write_text(xml, encoding='utf-8-sig')
config_file = CONF / 'Configuration.xml'
config = config_file.read_text(encoding='utf-8-sig')
if '<CommonForm>Автотесты</CommonForm>' not in config:
    config = config.replace('<CommonForm>РабочийСтол</CommonForm>', '<CommonForm>РабочийСтол</CommonForm>\n            <CommonForm>Автотесты</CommonForm>')
config = config.replace('<Version>1.2.5</Version>', '<Version>1.2.7</Version>').replace('<Version>1.2.6</Version>', '<Version>1.2.7</Version>')
config = config.replace('<v8:content>Молочная ферма</v8:content>', '<v8:content>Молочная ферма Луговая 1.2.7</v8:content>', 1)
if '<Subsystem>Тестирование</Subsystem>' not in config:
    config = config.replace('<Subsystem>Продажа</Subsystem>', '<Subsystem>Продажа</Subsystem>\n            <Subsystem>Тестирование</Subsystem>')
config_file.write_text(config, encoding='utf-8-sig')
subsystem_id = '05a33a3f-0bab-4abc-853a-e754251946d7'
subsystem = (CONF / 'Subsystems/Продажа.xml').read_text(encoding='utf-8-sig')
subsystem = subsystem.replace('97e2b442-00e3-5313-b9cd-d451758c552e', subsystem_id)
subsystem = subsystem.replace('<Name>Продажа</Name>', '<Name>Тестирование</Name>')
subsystem = subsystem.replace('<v8:content>Продажа</v8:content>', '<v8:content>Автотесты</v8:content>')
subsystem = subsystem.replace('CommonForm.ПанельПродажа', 'CommonForm.Автотесты')
(CONF / 'Subsystems/Тестирование.xml').write_text(subsystem, encoding='utf-8-sig')
rights_file = CONF / 'Roles/ПолныеПрава/Ext/Rights.xml'
rights = rights_file.read_text(encoding='utf-8-sig')
if '<name>CommonForm.Автотесты</name>' not in rights:
    match = re.search(r'<object>\s*<name>CommonForm\.РабочийСтол</name>.*?</object>', rights, re.S)
    rights = rights.replace('</Rights>', match.group(0).replace('РабочийСтол', 'Автотесты') + '\n</Rights>')
rights_file.write_text(rights, encoding='utf-8-sig')
if '<name>Subsystem.Тестирование</name>' not in rights:
    match = re.search(r'<object>\s*<name>Subsystem\.Продажа</name>.*?</object>', rights, re.S)
    rights = rights.replace('</Rights>', match.group(0).replace('Subsystem.Продажа', 'Subsystem.Тестирование') + '\n</Rights>')
rights_file.write_text(rights, encoding='utf-8-sig')
desktop_file = CONF / 'CommonForms/РабочийСтол/Ext/Form/Module.bsl'
desktop = desktop_file.read_text(encoding='utf-8-sig')
if 'Процедура ОткрытьАвтотесты' not in desktop:
    desktop = desktop.replace('    Подпись = Элементы.Добавить("ПорядокРаботы"', '''    Если РольДоступна("ПолныеПрава") Тогда
        Тестирование = ДобавитьВкладку(Разделы, "ТестированиеФермы", "Тестирование");
        ДобавитьКнопку("ОткрытьАвтотесты", "Автотесты: запустить проверки", Тестирование);
    КонецЕсли;
    Подпись = Элементы.Добавить("ПорядокРаботы"''')
    desktop += '''
&НаКлиенте
Процедура ОткрытьАвтотесты(Команда) Экспорт
    ОткрытьФорму("ОбщаяФорма.Автотесты");
КонецПроцедуры
'''
if 'Процедура ОткрытьАвтотестыНаГлавной' not in desktop:
    desktop = desktop.replace('    Разделы = Элементы.Добавить("РазделыРаботы"', '''    Если РольДоступна("ПолныеПрава") Тогда
        ПроверкаСистемы = ДобавитьГруппуКоманд(Неопределено, "ПроверкаСистемы", "Проверка работы системы");
        ДобавитьКнопку("ОткрытьАвтотестыНаГлавной", "Автотесты", ПроверкаСистемы);
        Подсказка = Элементы.Добавить("КакЗапуститьАвтотесты", Тип("ДекорацияФормы"), ПроверкаСистемы);
        Подсказка.Вид = ВидДекорацииФормы.Надпись;
        Подсказка.Заголовок = "Откройте список проверок и нажмите «Запустить 41 проверку». Результат появится в этой же странице.";
        Подсказка.Ширина = 100;
    КонецЕсли;
    Разделы = Элементы.Добавить("РазделыРаботы"''', 1)
    desktop += '''
&НаКлиенте
Процедура ОткрытьАвтотестыНаГлавной(Команда) Экспорт
    ОткрытьАвтотесты(Команда);
КонецПроцедуры
'''
desktop_file.write_text(desktop, encoding='utf-8-sig')
dump_file = CONF / 'ConfigDumpInfo.xml'
dump = dump_file.read_text(encoding='utf-8-sig')
if 'CommonForm.Автотесты' not in dump:
    entries = ''.join(f'\n<Metadata name="CommonForm.Автотесты{suffix}" id="{FORM_ID}{number}" configVersion="{version}"/>'
                      for suffix, number, version in [('', '', 'b'*35+'0000000'), ('.Form', '.0', 'c'*35+'0000000'), ('.Form.Module', '.0', 'd'*35+'0000000')])
    dump = dump.replace('</ConfigVersions>', entries + '\n</ConfigVersions>')
dump_file.write_text(dump, encoding='utf-8-sig')
if 'Subsystem.Тестирование' not in dump:
    dump = dump.replace('</ConfigVersions>', f'<Metadata name="Subsystem.Тестирование" id="{subsystem_id}" configVersion="' + 'e'*35 + '0000000"/>\n</ConfigVersions>')
    dump_file.write_text(dump, encoding='utf-8-sig')

# A verification hook invokes precisely the command used by the UI, twice.
hook = '''
    Если Лев(ПараметрЗапуска, 18) = "FarmEmbeddedTests=" Тогда
        Файл = Новый ЗаписьТекста(Сред(ПараметрЗапуска, 19) + "/embedded-tests.txt", КодировкаТекста.UTF8);
        Попытка
            До = СервисФермы.СнимокДанныхДляАвтотестов();
            Файл.ЗаписатьСтроку(СервисФермы.ПроверитьЗащитуОтЛожногоУспеха());
            Главная = ПолучитьФорму("ОбщаяФорма.РабочийСтол");
            Если Главная.Команды.Найти("ОткрытьАвтотестыНаГлавной") = Неопределено Тогда
                ВызватьИсключение "На стартовом рабочем столе нет кнопки Автотесты";
            КонецЕсли;
            Главная.ОткрытьАвтотестыНаГлавной(Неопределено);
            Файл.ЗаписатьСтроку("PASS | Кнопка Автотесты на главной открывает экран проверок");
            Форма = ПолучитьФорму("ОбщаяФорма.Автотесты");
            Форма.Открыть();
            Для Номер = 1 По 2 Цикл
                Форма.ЗапуститьТесты(Неопределено);
                Файл.ЗаписатьСтроку("RUN " + Строка(Номер));
                Файл.ЗаписатьСтроку(Форма.ТекстПротокола);
                Если Не Форма.Успешно Или Форма.Пройдено <> 41 Тогда ВызватьИсключение "Встроенный набор не прошел"; КонецЕсли;
                Если До <> СервисФермы.СнимокДанныхДляАвтотестов() Тогда ВызватьИсключение "Данные базы изменились после теста"; КонецЕсли;
                Файл.ЗаписатьСтроку("PASS | Данные базы сохранены после запуска " + Строка(Номер));
                ДругаяФорма = ПолучитьФорму("ОбщаяФорма.ПанельПродажа");
                ДругаяФорма.Открыть();
                Форма.ПроверитьУходСоСтраницы();
                Если Форма.Успешно Или Форма.Пройдено <> 0 Или Не ПустаяСтрока(Форма.ТекстПротокола)
                    Или Форма.Результат.Область(2, 1).Текст <> "НЕ ЗАПУЩЕН" Тогда
                    ВызватьИсключение "Результат не сброшен после ухода со страницы";
                КонецЕсли;
                Файл.ЗаписатьСтроку("PASS | Уход со страницы сбрасывает результат и сохраняет описания");
                ДругаяФорма.Закрыть();
                Форма.Закрыть();
                Форма = ПолучитьФорму("ОбщаяФорма.Автотесты");
                Форма.Открыть();
                Если Форма.Успешно Или Форма.Пройдено <> 0 Или Не ПустаяСтрока(Форма.ТекстПротокола)
                    Или Форма.Результат.Область(2, 1).Текст <> "НЕ ЗАПУЩЕН" Тогда
                    ВызватьИсключение "Повторное открытие восстановило старый результат";
                КонецЕсли;
                Файл.ЗаписатьСтроку("PASS | После закрытия и открытия все проверки не запущены");
            КонецЦикла;
            Файл.ЗаписатьСтроку("COMPLETE");
        Исключение
            Файл.ЗаписатьСтроку("ERROR | " + ОписаниеОшибки());
        КонецПопытки;
        Файл.Закрыть();
        ЗавершитьРаботуСистемы(Ложь);
        Возврат;
    КонецЕсли;
'''
if 'FarmEmbeddedTests=' in app:
    first = app.index('    Если Лев(ПараметрЗапуска, 18) = "FarmEmbeddedTests="')
    last = app.index('    Если Лев(ПараметрЗапуска, 18) = "FarmScheduleTests="', first)
    app = app[:first] + hook.lstrip('\n') + app[last:]
else:
    app = app.replace('Процедура ПриНачалеРаботыСистемы()', 'Процедура ПриНачалеРаботыСистемы()' + hook, 1)
app_file.write_text(app, encoding='utf-8-sig')
print('Embedded test screen wired into configuration 1.2.7')
