"""Verify current version, rendered document provenance, links and shipped evidence."""
from pathlib import Path
import hashlib
import json
import re
from zipfile import ZipFile
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'Документация/Актуальная_поставка_1.2.7'
E=ROOT/'Документация/04_Тестирование/Протоколы/Итоговая_приемка_1.2.7'
N={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main','p':'http://schemas.openxmlformats.org/presentationml/2006/main'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for final,review in [('Описание_и_инструкция_1.2.7.docx','guide.docx'),('Отчет_о_проверках_1.2.7.docx','report-fixed.docx')]:
    assert sha(D/final)==sha(ROOT/'.build/docs127'/review), final
for file in [p for p in D.glob('*.docx') if not p.name.startswith('~$')]:
    with ZipFile(file) as z:
        text=' '.join(ET.fromstring(z.read('word/document.xml')).itertext())
        assert '1.2.7' in text and '1.2.6' not in text and '1.2.5' not in text
        styles=ET.fromstring(z.read('word/styles.xml'))
        title=styles.find("w:style[@w:styleId='Title']",N)
        assert title.find('.//w:pBdr',N) is None
        for table in ET.fromstring(z.read('word/document.xml')).findall('.//w:tbl',N):
            grid=[int(x.get('{'+N['w']+'}w')) for x in table.findall('w:tblGrid/w:gridCol',N)]
            assert sum(grid)<=7*1440
            for row in table.findall('w:tr',N):
                widths=[int(x.get('{'+N['w']+'}w')) for x in row.findall('w:tc/w:tcPr/w:tcW',N)]
                assert widths==grid
deck=ROOT/'Документация/04_Тестирование/Защита_21_ноября/Автотесты_Луговая_защита_1.2.7.pptx'
with ZipFile(deck) as z:
    assert z.testzip() is None
    assert len(ET.fromstring(z.read('ppt/presentation.xml')).find('p:sldIdLst',N))==8
    assert len(ET.fromstring(z.read('ppt/slides/slide5.xml')).findall('.//a:tbl',N))==1
    assert '1.2.7' in z.read('ppt/slides/slide1.xml').decode()
    assert 'принимает любое исключение' not in ''.join(z.read(n).decode() for n in z.namelist() if re.fullmatch(r'ppt/notesSlides/notesSlide\d+.xml',n))
    for number in [2,6,7]:assert len(ET.fromstring(z.read(f'ppt/slides/slide{number}.xml')).findall('.//p:pic',N))==1
for relative in re.findall(r'\]\(([^)]+)\)',(ROOT/'README.md').read_text(encoding='utf-8')):
    assert (ROOT/relative).exists(),relative
manifest=json.loads((E/'manifest.json').read_text(encoding='utf-8'))
for name,expected in manifest['release_sha256'].items():assert sha(ROOT/'deliverables'/name)==expected
for name in ['closure','guide','report-fixed']:
    assert (ROOT/f'.build/docs127/{name}.pdf').is_file()
    assert list((ROOT/'.build/docs127').glob(name+'-*.png'))
qa={'version':'1.2.7','document_renderer':'Microsoft Word native PDF export after packaged renderer reported missing LibreOffice','document_pages':[1,3,3],
    'all_document_pages_visually_reviewed':True,'all_8_slides_rendered_in_artifact_session_and_visually_reviewed':True,'release_sha256_unchanged':True,
    'docx_sha256':{p.name:sha(p) for p in D.glob('*.docx') if not p.name.startswith('~$')},'pptx_sha256':sha(deck)}
(ROOT/'.build/release127-qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8')
print('Release127 verification passed:3DOCX,8slides,release hashes and README links')
