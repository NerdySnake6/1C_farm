"""Update Ivanov's project documents with current scope and evidence.

The reviewed source revision is immutable; repeated builds produce the same
content without appending duplicate sections or replacing the author's model.
Run build_all_documentation.render_and_sync after building for final page numbers.
"""

from io import BytesIO
from pathlib import Path
import argparse
import subprocess
import sys
from urllib.parse import quote

from docx import Document
from docx.opc.constants import RELATIONSHIP_TYPE
from docx.enum.text import WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'Документация/07_Управление_проектом'
SOURCE_REF = '98bd98cfef5d8efe5c87653d6d41019899d649bc'
PROTOCOLS = '../04_Тестирование/Протоколы/'


def page(document, title):
    """Start a major section on its own page."""
    item = document.add_heading(title, level=1)
    item.paragraph_format.page_break_before = True
    return item


def text(document, value):
    """Append one explanatory paragraph in the existing style."""
    return document.add_paragraph(value)


def table(document, headers, rows, widths):
    """Add a compact matrix with repeatable headers and flexible row heights."""
    grid = document.add_table(rows=1, cols=len(headers))
    grid.autofit = False
    for col, width in zip(grid.columns, widths):
        col.width = Cm(width)
    for cell, value in zip(grid.rows[0].cells, headers):
        cell.text = value
    grid.rows[0]._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))
    for values in rows:
        for cell, value in zip(grid.add_row().cells, values):
            cell.text = value
    for i, row in enumerate(grid.rows):
        row._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
        for cell, width in zip(row.cells, widths):
            cell.width = Cm(width)
            properties = cell._tc.get_or_add_tcPr()
            borders = OxmlElement('w:tcBorders')
            for edge in ['top', 'left', 'bottom', 'right']:
                border = OxmlElement('w:' + edge)
                for key, value in [('val', 'single'), ('sz', '4'), ('color', 'D9D9D9')]:
                    border.set(qn('w:' + key), value)
                borders.append(border)
            properties.append(borders)
            margins = OxmlElement('w:tcMar')
            for edge in ['top', 'bottom', 'left', 'right']:
                margin = OxmlElement('w:' + edge)
                margin.set(qn('w:w'), '70')
                margin.set(qn('w:type'), 'dxa')
                margins.append(margin)
            properties.append(margins)
            if i == 0:
                fill = OxmlElement('w:shd')
                fill.set(qn('w:fill'), 'DCE6F1')
                properties.append(fill)
            for item in cell.paragraphs:
                item.paragraph_format.space_after = Pt(3)
                item.paragraph_format.line_spacing = 1.05
                for run in item.runs:
                    run.font.size = Pt(9)
                    run.bold = i == 0
    document.add_paragraph().paragraph_format.space_after = Pt(2)
    return grid


def current_scope(document, is_plan):
    """Separate delivered functionality from the commercial planning model."""
    page(document, 'Актуальный объём проекта')
    text(document, 'Редакция документа 1.1 от 3 ноября 2026 года. Автор — Иванов Федор Владиславович. '
         'Руководитель проекта — Калинин Игорь Вячеславович. Текущая конфигурация — 1.2.1; '
         'платформа — 1С 8.3.27.1688, учебная версия, файловая база под macOS.')
    text(document, 'Учебная поставка учитывает готовую молочную продукцию: молоко, творог и сметану. '
         'Она содержит поступление, продажу, бронирование, цены, фотографии и отчёты. '
         'Приёмка этой поставки опирается на исходники, DT/CF и сохранённые протоколы испытаний.')
    table(document, ['Область', 'Учебная поставка 1.2.1', 'Коммерческая модель развития'], [
        ('Предмет учёта', 'Готовая молочная продукция; приход, расход, резерв', 'Животные, культуры, корма, партии и себестоимость'),
        ('Среда', 'Файловая база, учебная платформа, macOS', 'Клиент-сервер, PostgreSQL, облако и веб-интерфейс'),
        ('Сроки', 'Имеются прогоны 23–29 октября; фактический статус — по протоколам', 'Плановый срез 01.08.2026; горизонт до 31.12.2026'),
        ('Финансы', 'Фактические расходы учебной команды не учтены', 'Расчётный лимит 8,4 млн руб.; коммерческие предложения не приложены'),
    ], [2.4, 7.1, 7.4])
    text(document, 'Нумерованные разделы ' + ('1–15' if is_plan else '1–7') +
         ' ниже сохраняют коммерческую модель Иванова. Её сроки, роли заказчика и подрядчика, '
         'критерии AC01–AC06, закупки и экономический эффект относятся к планируемому расширению. '
         'Они не подтверждают наличие этих функций в учебной поставке и не являются её условиями сдачи.')
    text(document, 'Частичная выдача по брони, производство, животные, растениеводство, партии, '
         'инвентаризация, себестоимость, HTTP API и веб-витрина в текущий объём не входят. '
         'СрокБрони и процедура снятия просроченных броней реализованы. Автоматический запуск '
         'требует настройки существующего задания в базе: ежедневное повторение каждые 60 секунд '
         'и открытый клиент в файловом режиме. Настройка подтверждена только в отдельной тестовой базе.')
    text(document, 'Ближайший результат — согласованный комплект исходников 1.2.1, DT/CF, инструкции '
         'и протоколов. Для изменения объёма развития требуется отдельное решение с оценкой '
         'трудоёмкости, приёмки и ресурсов. Плановая дата не заменяет фактическую дату выполнения.')


def acceptance(document):
    """Link actual metadata and existing checks without inventing test results."""
    page(document, 'Приёмка учебной конфигурации')
    text(document, 'Коды UC относятся к текущей поставке и не заменяют AC01–AC06 коммерческой модели. '
         'Решение о сдаче принимается по результатам и ограничениям конкретного прогона. '
         'Ссылки на документы и протоколы приведены в разделе «Материалы и навигация».')
    table(document, ['Требование', 'Объекты 1С', 'Проверка и критерий', 'Доказательство'], [
        ('UC01 Продукция и цены', 'Номенклатура; Цены', 'MP01, MP02: фото сохраняется; цена соответствует дате', 'Отчёт: раздел 4; MP01-card.png, MP02-prices.png'),
        ('UC02 Поступление', 'Приход; ОстаткиПродукции', 'MP03: 2 л дают 77 л; отмена возвращает 75 л; перепроведение без дублей', 'MP03-stock.png; приложение Г отчёта'),
        ('UC03 Продажа', 'Расход; ОстаткиПродукции', 'MS01: 1 л даёт 74 л; отмена восстанавливает 75 л', 'MS01-sale.png; приложение Г отчёта'),
        ('UC04 Резерв и отказ', 'Бронирование; РезервыПродукции', 'B01–B06, MS02, MS04: бронь 20 л даёт 75/20/55; продажа 56 л отклоняется', 'reservation-tests.txt; MS02-booked.png; MS04-message-1.png'),
        ('UC05 Продать или отменить', 'Бронирование; Расход; оба регистра', 'B14–B20, MS02–MS03: отмена 75/0/75; продажа 55/0/55; повтор запрещён', 'reservation-tests.txt; MS02-cancelled.png; MS03-linked-sale.png'),
    ], [3.0, 3.9, 6.1, 3.9])
    text(document, 'Порядок чисел в UC04–UC05: на складе / в резерве / свободно. '
         'Исходный остаток молока — 75 л; творога — 15 кг; сметаны — 12 кг; резервы — ноль. '
         'Цены — 90, 360 и 280 руб.; исходная выручка — 4 890 руб. '
         'Разные ветви проверки выполняются независимо с возвратом к исходным данным.')
    page(document, 'Приёмка прав и срока брони')
    table(document, ['Требование', 'Объекты 1С', 'Критерий и состояние', 'Доказательство'], [
        ('UC06 Права', 'Покупка; Продажа; ПолныеПрава', 'MA02; DEF-001/002: разрешённые документы изменяются и отменяются; чужие операции ограничены', 'Исправление_DEF-001_DEF-002; приложение Г отчёта'),
        ('UC07 Срок брони', 'СрокБрони; СнятьПросроченныеБрони; УчетФермы', 'Просроченная бронь снимается, будущая остаётся. Успешно после настройки расписания в тестовой базе', 'Расписание_брони_20261029/scheduler-run.txt'),
        ('UC08 Отчёты и восстановление', 'ОстаткиПродукции; ПродажиЗаПериод; ДоступностьПродукции', 'MS05, MA03: исходные остатки и выручка; DT восстанавливается. Отдельная ручная проверка нового отчёта не заявляется', 'MS05-stock.png; MS05-sales.png; Проверка_DT; исходники отчётов'),
    ], [2.8, 4.1, 6.0, 4.0])
    text(document, 'В отчёте Ефимова С.Р. журнал SM01–SM12 заполнен в коммите 5326e91; '
         'ручные результаты принадлежат указанному исполнителю. Дополнение от 29 октября '
         'не называет точную версию повторной ручной базы. Автоматизация 1.2.1 содержит '
         '55 проверок форм и прав и 83 проверки регрессии; повторные прогоны не прибавляются '
         'как новые уникальные тесты. Это сведения о выполненных испытаниях, а не новый прогон 3 ноября.')
    text(document, 'Проверка расписания — отдельный автоматический опыт с реальным ожиданием. '
         'При исходном интервале 0 секунд просроченная бронь оставалась проведённой через 70 секунд. '
         'После настройки интервала 60 секунд планировщик снял её проведение; будущая бронь сохранилась. '
         'Исправление расписания рабочей базы и обновлённая поставка этим опытом не подтверждаются.')
    text(document, 'Перед показом ответственный за сборку проверяет версию DT/CF, дату отчётов, '
         'нулевой резерв и расписание в используемой копии. QA фиксирует результаты повторяемых '
         'проверок; руководитель принимает комплект с указанными ограничениями. '
         'Печать в установленной учебной лицензии ограничена: успешное отображение отчёта '
         'не означает успешной печати. Открытые вопросы оформляются в реестре, а не закрываются '
         'плановым статусом AC коммерческой модели.')


def financial_basis(document, is_plan):
    """Explain the preserved estimate and the data needed to substantiate it."""
    page(document, 'Приложение А Основания расчётной модели')
    text(document, 'Бюджет и эффект сохранены из модели Иванова для сравнения вариантов расширения. '
         'Это не расходы учебной команды, не согласованная смета внедрения и не текущие рыночные цены. '
         'Суммы не заменяют договоры, табели и предложения поставщиков. '
         'Расчётный срез — 1 августа 2026 года; проверка актуальности требуется перед решением о финансировании.')
    table(document, ['Статья', 'Расчёт в модели', 'Что нужно подтвердить'], [
        ('Труд', '(220 + 300 + 210 + 180) тыс. × 5 мес. = 4 550 тыс.', 'Задачи, трудоёмкость и доступность четырёх участников; основание ставок'),
        ('Начисления', '4 550 × 30% = 1 365 тыс.', 'Коэффициент 30% — допущение; расчёт для выбранной формы найма'),
        ('Закупки и услуги', 'Лицензии 320; облако 100; веб 900; обучение 60 тыс.', 'Состав лицензий, параметры стенда, сопоставимые предложения и спецификация веб-работ'),
        ('Прямые затраты', '4 550 + 1 365 + 320 + 100 + 900 + 60 = 7 295 тыс.', 'Сверка состава работ; отсутствие двойной оплаты труда и услуг'),
        ('Резервы', '705 тыс. на риски + 400 тыс. управленческий', 'Обоснование реакций и стоимости; решение владельца резерва'),
        ('Общий лимит', 'BAC 8 000 + 400 = 8 400 тыс.', '7 295 + 705 = 8 000; подтверждение бюджета и источника средств'),
    ], [2.7, 6.4, 7.8])
    text(document, '705 тыс. руб. распределены по рискам R01–R09 как лимиты реагирования, '
         'а не рассчитаны по статистике потерь. До утверждения требуется оценить стоимость '
         'конкретных мер; совпадение суммы с резервом само по себе достаточность резерва не доказывает. '
         '400 тыс. руб. находятся вне BAC. Финансовые допущения проверяются отдельно от сдачи учебной базы.')
    page(document, 'Приложение А1 Проверка ожидаемого эффекта')
    text(document, 'В модели валовой месячный эффект — 450 тыс. руб.: снижение потерь 200 тыс., '
         'экономия труда 100 тыс. и дополнительная маржа 150 тыс. Эксплуатация — 50 тыс. '
         'Чистый эффект — 400 тыс. руб. Начало эффекта с 01.02.2027 является допущением, '
         'а не результатом эксплуатации учебной конфигурации.')
    if is_plan:
        table(document, ['Слагаемое', 'Способ обоснования', 'Данные и проверяющий'], [
            ('Потери 200 тыс.', 'Сопоставимый оборот × снижение доли потерь; исключить сезонность', 'Оборот, списания и причины до/после; управляющий'),
            ('Труд 100 тыс.', 'Подтверждённая экономия часов × стоимость часа; отделить время от денежной экономии', 'Замеры операций и ставка часа; бухгалтер'),
            ('Маржа 150 тыс.', 'Дополнительные продажи × маржинальность; исключить эффект, уже учтённый в потерях', 'Продажи, переменные затраты, возвраты; руководитель сбыта'),
            ('Эксплуатация 50 тыс.', 'Облако 20 + сопровождение 30 тыс.; проверить полноту', 'Предложения, объём поддержки и резервирования; ИТ и PM'),
        ], [3.0, 7.1, 6.8])
    table(document, ['Доля валового эффекта', 'Чистый эффект в месяц', 'Простая окупаемость'], [
        ('100%', '450 − 50 = 400 тыс.', '8 400 / 400 = 21 месяц'),
        ('70%', '315 − 50 = 265 тыс.', '8 400 / 265 = 31,7 месяца'),
        ('50%', '225 − 50 = 175 тыс.', '8 400 / 175 = 48 месяцев'),
    ], [5.0, 6.0, 5.9])
    text(document, 'Расчёт не учитывает дисконтирование, разгон эффекта и изменение затрат. '
         'Показатель за 36 месяцев при полном эффекте: (14,4 − 8,4) / 8,4 = 71,4%. '
         'Для решения по реальному внедрению нужны подтверждённые исходные данные и денежный поток. '
         'Ответственные проверяют допущения до выделения средств; неподтверждённые значения остаются оценками. '
         'Контроль выгод через 3, 6 и 12 месяцев применяется только после фактического запуска расширения.')


def navigation(document):
    """List real relative paths and the recommended order of use."""
    page(document, 'Материалы и навигация')
    text(document, 'Порядок чтения: актуальный объём → приёмка учебной конфигурации в плане → '
         'инструкция пользователя и отчёт испытаний → коммерческая модель и её финансовые основания. '
         'Нумерованные главы описывают развитие; фактическую готовность следует проверять по протоколам.')
    grid = table(document, ['Материал', 'Путь от папки 07_Управление_проектом'], [
        ('Устав и план', 'Устав_проекта.docx; План_управления_проектом.docx'),
        ('Общее описание', '../01_Общее_описание/Общая_документация.docx'),
        ('Инструкция', '../03_Пользователю/Инструкция_пользователя.docx'),
        ('Отчёт испытаний', '../04_Тестирование/Документация_по_тестированию.docx'),
        ('Протоколы UC01–UC05', PROTOCOLS + 'reservation-tests.txt; Ручные/RUN-20261028-01/'),
        ('Права и восстановление', PROTOCOLS + 'Исправление_DEF-001_DEF-002/'),
        ('Расписание', PROTOCOLS + 'Расписание_брони_20261029/'),
        ('Исходники и поставка', '../../configuration/; ../../deliverables/Farm_Lugovaya_v1.2.1.dt и .cf'),
    ], [4.3, 12.6])
    destinations = [
        ['Устав_проекта.docx', 'План_управления_проектом.docx'],
        ['../01_Общее_описание/Общая_документация.docx'],
        ['../03_Пользователю/Инструкция_пользователя.docx'],
        ['../04_Тестирование/Документация_по_тестированию.docx'],
        [PROTOCOLS + 'reservation-tests.txt', PROTOCOLS + 'Ручные/RUN-20261028-01/'],
        [PROTOCOLS + 'Исправление_DEF-001_DEF-002/'],
        [PROTOCOLS + 'Расписание_брони_20261029/'],
        ['../../configuration/', '../../deliverables/Farm_Lugovaya_v1.2.1.dt',
         '../../deliverables/Farm_Lugovaya_v1.2.1.cf'],
    ]
    for row, paths in zip(grid.rows[1:], destinations):
        cell = row.cells[1]
        cell.text = ''
        for index, relative in enumerate(paths):
            assert (FOLDER / relative).exists(), relative
            item = cell.paragraphs[0] if index == 0 else cell.add_paragraph()
            item.paragraph_format.space_after = Pt(3)
            link = OxmlElement('w:hyperlink')
            relation = document.part.relate_to(quote(relative), RELATIONSHIP_TYPE.HYPERLINK,
                                               is_external=True)
            link.set(qn('r:id'), relation)
            run = OxmlElement('w:r')
            properties = OxmlElement('w:rPr')
            size = OxmlElement('w:sz')
            size.set(qn('w:val'), '18')
            properties.append(size)
            run.append(properties)
            value = OxmlElement('w:t')
            value.text = relative
            run.append(value)
            link.append(run)
            item._p.append(link)
    text(document, 'Версии документов хранятся в Git. Основная папка текущих материалов — '
         'Документация/07_Управление_проектом. Предыдущая редакция Иванова доступна в коммите 98bd98c. '
         'Повторная сборка: scripts/build_project_management.py; рендер и синхронизация содержания '
         'выполняются перед передачей DOCX. PDF применяется только для внутренней проверки.')


def add_contents(document, anchor):
    """Insert linked contents and stable heading bookmarks before the main text."""
    heading = document.add_heading('Содержание', level=1)
    heading.paragraph_format.page_break_before = False
    anchor.addprevious(heading._p)
    targets = [p for p in document.paragraphs if p.style.name == 'Heading 1' and p.text != 'Содержание']
    for i, target in enumerate(targets):
        name = f'pm_chapter_{i}'
        begin = OxmlElement('w:bookmarkStart')
        begin.set(qn('w:id'), str(7000 + i))
        begin.set(qn('w:name'), name)
        end = OxmlElement('w:bookmarkEnd')
        end.set(qn('w:id'), str(7000 + i))
        target._p.insert(1, begin)
        target._p.append(end)
        item = document.add_paragraph()
        item.paragraph_format.space_after = Pt(5)
        item.paragraph_format.line_spacing = 1.05
        item.paragraph_format.tab_stops.add_tab_stop(Cm(16.8), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
        link = OxmlElement('w:hyperlink')
        link.set(qn('w:anchor'), name)
        run = OxmlElement('w:r')
        value = OxmlElement('w:t')
        value.text = target.text
        run.append(value)
        link.append(run)
        item._p.append(link)
        item.add_run('\t')
        item.add_run('0')
        anchor.addprevious(item._p)


def build():
    """Build both reviewed documents while retaining the original model and author."""
    for name in ['Устав_проекта.docx', 'План_управления_проектом.docx']:
        path = FOLDER / name
        relative = str(path.relative_to(ROOT))
        original = subprocess.check_output(['git', 'show', SOURCE_REF + ':' + relative], cwd=ROOT)
        document = Document(BytesIO(original))
        is_plan = name.startswith('План')
        anchor = document.paragraphs[10]._p
        for p in document.paragraphs:
            if p.text == 'Проектная документация по PMBOK 5':
                p.text = 'Учебная поставка и модель развития по PMBOK 5'
            if 'Плановый срез 01 августа 2026 года' in p.text:
                p.text = 'Модель развития на 01.08.2026 • Редакция документа 1.1 от 03.11.2026'
            if 'PM хранит версии в docs_pmbok' in p.text:
                p.text = p.text.replace('PM хранит версии в docs_pmbok',
                                        'PM хранит версии в Документация/07_Управление_проектом')
        start = len(document.element.body) - 1
        current_scope(document, is_plan)
        if is_plan:
            acceptance(document)
        else:
            text(document, 'Критерии UC01–UC08 и связь с действующими тестами приведены в плане '
                 'управления проектом, разделы приёмки учебной конфигурации. '
                 'Для учебной сдачи используются эти критерии; AC01–AC06 ниже относятся к развитию.')
        nodes = list(document.element.body)[start:-1]
        for node in nodes:
            anchor.addprevious(node)
        old_title = document.paragraphs[[p._p for p in document.paragraphs].index(anchor)]
        old_title.paragraph_format.page_break_before = True
        title = text(document, 'Далее приведена коммерческая модель развития. '
                     'Её условия не входят автоматически в текущую поставку 1.2.1.')
        anchor.addnext(title._p)
        financial_basis(document, is_plan)
        navigation(document)
        add_contents(document, nodes[0])
        for style_name in ['Title', 'Heading 1', 'Heading 2']:
            document.styles[style_name].font.color.rgb = RGBColor(0, 0, 0)
        document.core_properties.version = '1.1'
        document.save(path)
        print(path)


def main():
    """Build and optionally render both documents with synchronized contents."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--render', action='store_true')
    args = parser.parse_args()
    build()
    if args.render:
        from build_all_documentation import synchronize_contents

        renderer = Path('/Users/nerdysnake6/.codex/plugins/cache/openai-primary-runtime/'
                        'documents/26.1026.10807/skills/documents/render_docx.py')
        for path in sorted(FOLDER.glob('*.docx')):
            output = ROOT / '.build/project-management' / path.stem
            command = [sys.executable, str(renderer), str(path), '--output_dir',
                       str(output), '--emit_pdf']
            subprocess.run(command, check=True)
            synchronize_contents(path, next(output.glob('*.pdf')))
            subprocess.run(command, check=True)


if __name__ == '__main__':
    main()
