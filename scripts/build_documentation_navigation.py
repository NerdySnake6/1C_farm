"""Build a direct-file index and a short reservation demonstration guide."""
from urllib.parse import quote

from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE
from docx.shared import Pt

from document_common import DOC_ROOT, FACTS, OUTPUTS, new_document, page, paragraph, save_document, table


def file_link(document, target, label):
    """Add a portable relative link to a project file."""
    relation=document.part.relate_to(quote(target),RELATIONSHIP_TYPE.HYPERLINK,is_external=True)
    item=document.add_paragraph()
    link=OxmlElement('w:hyperlink')
    link.set(qn('r:id'),relation)
    run=OxmlElement('w:r')
    properties=OxmlElement('w:rPr')
    underline=OxmlElement('w:u')
    underline.set(qn('w:val'),'single')
    properties.append(underline)
    run.append(properties)
    value=OxmlElement('w:t')
    value.text=label
    run.append(value)
    link.append(run)
    item._p.append(link)


def build():
    """Create a two-page index that opens each deliverable without a ZIP."""
    doc=new_document('Навигация по комплекту')
    doc.sections[0].different_first_page_header_footer=False
    title=doc.add_paragraph('Материалы проекта Молочная ферма Луговая',style='Title')
    for run in title.runs:
        run.font.size=Pt(24)
    paragraph(doc,'Молочная ферма Луговая. Версия '+FACTS['source_configuration_version']+'. Руководитель проекта: '+FACTS['author']+'.')
    paragraph(doc,'Откройте нужный документ по ссылке ниже. Актуальные материалы доступны отдельными файлами в папке Документация.')
    doc.add_heading('Результат доработки',level=2)
    table(doc,['Состояние молока','Склад','Резерв','Свободно'],[
        ('До брони','75 л','0 л','75 л'),('Бронь 20 л','75 л','20 л','55 л'),
        ('Продажа по брони','55 л','0 л','55 л'),('Отмена до продажи','75 л','0 л','75 л'),
    ],[3.2,1.15,1.15,1.15])
    paragraph(doc,'Продажа и отмена — альтернативные ветви. Обычная продажа 56 л при свободных 55 л отклоняется.')
    doc.add_heading('Открыть материалы',level=2)
    for key,label,description in [
        ('presentation','Презентация PowerPoint','Обзор проекта на 11 слайдах: назначение, структура, интерфейс, учёт, бронирование и проверки. Заметки на выступление до пяти минут.'),
        ('general','Общая документация Word','Обзор изменений на странице аннотации; структура и алгоритмы, подробная модель брони в разделе 9.'),
        ('user','Инструкция пользователя Word','Бронирование и проверка результатов находятся в разделах 2–3, сразу после входа.'),
        ('testing','Документация по тестированию Word','Smoke-тест в разделе 3; подробные сценарии по ролям в разделах 4–6; журнал и дефекты в разделе 8. Автоматические результаты в приложении А.'),
        ('design','Обоснование дизайна Word','Оформление новых команд, состояния и отчёта рассматривается в первом разделе.'),
    ]:
        file_link(doc, OUTPUTS[key].relative_to(DOC_ROOT).as_posix(), label)
        paragraph(doc,description)
    page(doc,'Короткая демонстрация на занятии')
    for index,text in enumerate([
        'Открыть отчёт исходного примера: молоко на складе 75 л, резерв 0, свободно 75 л.',
        'В Продаже создать и провести бронь 20 л. В отчёте проверить 75, 20 и 55.',
        'Попробовать обычную продажу 56 л. Показать отказ и сохранение остатков.',
        'Отменить бронь. Показать, что все 75 л снова свободны.',
        'Снова провести бронь и нажать «Продать по брони». Показать связанный Расход и остатки 55, 0 и 55.',
    ],1):
        paragraph(doc,f'{index}. {text}')
    paragraph(doc,'Демонстрация выполняется в отдельной копии базы. Чтобы вернуть исходное состояние после продажи, сначала отмените проведение Расхода, затем отмените бронь.')
    doc.add_heading('Поставка и результаты проверок', level=2)
    file_link(doc, '../deliverables/Farm_Lugovaya_v1.2.2.dt', 'Демонстрационная база 1.2.2')
    file_link(doc, '04_Тестирование/Протоколы/Поставка_1.2.2/README.md', 'Проверки поставки 1.2.2')
    paragraph(doc, 'Бронь продаётся целиком. Просроченные брони снимаются регламентным заданием. '
              'Интервал задания — 60 секунд. При демонстрации используйте свежую копию DT.')
    doc.add_heading('Управление проектом и вклад команды', level=2)
    file_link(doc, '07_Управление_проектом/Устав_проекта.docx', 'Устав проекта')
    file_link(doc, '07_Управление_проектом/План_управления_проектом.docx', 'План управления проектом')
    file_link(doc, '04_Тестирование/Официальный_ответ_на_претензию.docx', 'Официальный ответ на претензию')
    paragraph(doc, 'Калинин И. В. руководил проектом и подготовил исходную конфигурацию. '
              'Иванов Ф. В. добавил отчёт о доступности и задание снятия брони, подготовил устав и план.')
    paragraph(doc, 'Ефимов С. Р. провёл ручные проверки и доработал поставку по претензии. '
              'Истрашкин М. Д. подготовил редакции описания системы и дизайна. '
              'Варианты презентации добавил участник az299best.')
    file_link(doc, '../README.md', 'Вклад команды и ссылки на коммиты в README')
    save_document(doc,'navigation','Бронирование продукции Навигация по комплекту')


if __name__=='__main__':
    build()
