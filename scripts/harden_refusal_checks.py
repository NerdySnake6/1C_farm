"""Expose business rejection reasons through exceptions, preserving rollback."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
files = [*list((ROOT / 'configuration/Documents').glob('*/Ext/ObjectModule.bsl')),
         ROOT / 'configuration/CommonModules/УчетФермы/Ext/Module.bsl']
for path in files:
    text = path.read_text(encoding='utf-8-sig')
    text, count = re.subn(r'Сообщить\((.*?)\);', r'ВызватьИсключение \1;', text, flags=re.S)
    if count:
        path.write_text(text, encoding='utf-8-sig')
        print(f'{path.relative_to(ROOT)}: {count} business rejections')

path = ROOT / 'configuration/Ext/ManagedApplicationModule.bsl'
text = path.read_text(encoding='utf-8-sig')
old = 'Попытка ФормаБрони.ПродатьБронь(Неопределено); Исключение ОтказПовтора = Истина; КонецПопытки;'
new = '''Попытка
                ФормаБрони.ПродатьБронь(Неопределено);
            Исключение
                ОшибкаПовтора = ИнформацияОбОшибке();
                Пока ОшибкаПовтора.Причина <> Неопределено Цикл ОшибкаПовтора = ОшибкаПовтора.Причина; КонецЦикла;
                ОтказПовтора = СервисФермы.ПричинаСовпадает(ОшибкаПовтора.Описание,
                    "По этой брони уже есть проведённая продажа.");
            КонецПопытки;'''
text = text.replace(old, new)
text = text.replace('PASS | BF03 Повторная команда продажи отклонена"',
                    'PASS | BF03 Повторная команда продажи отклонена [Ожидаемый отказ подтвержден: по этой брони уже есть продажа]"')
path.write_text(text, encoding='utf-8-sig')
