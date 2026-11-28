"""Verify configured Serena over stdio; run with Serena's venv Python (mcp, PyYAML).

Does not launch 1C or change BSL. Refreshes only the project's thematic memories
and writes diagnostic evidence to ignored .build/serena-check/.
"""
import asyncio
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tomllib

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.build/serena-check'
MODULE = 'configuration/CommonModules/УчетФермы/Ext/Module.bsl'
MEMORIES = {
    'project_overview': '# Проект\nУчебная Молочная ферма Луговая, 1С/BSL/XML, версия 1.2.7. '
    'Текущая реализация: configuration/, старт Ext/ManagedApplicationModule.bsl; '
    'общие модули УчетФермы и СервисФермы. Карта и решения: docs/architecture.md; '
    'правила: AGENTS.md. Graphify не использовать. После существенных изменений '
    'обновлять основной документ и соответствующую короткую заметку. Проверять код, не полагаться на память.',
    'commands_and_testing': '# Команды и тестирование\nСм. docs/testing.md — основной источник команд, '
    'версий и условий. python scripts/test_defense_runner.py: 2 теста валидатора OK 26.11.2026. '
    'Встроенные 41 BSL-проверка и Farm* уже существуют; исторические результаты не являются '
    'новым прогоном. Vanessa Single 1.2.043.45: docs/vanessa.md. '
    'Три UI-сценария: tests/vanessa/; результаты: docs/status.md. '
    'run_vanessa_tests.py создаёт новую базу из DT 1.2.7 и текущих XML. Тесты — в явно определённой '
    'отдельной тестовой базе. Секреты не сохранять. Обновлять эту заметку при изменении окружения/команд.',
    'conventions': '# Соглашения\nAGENTS.md — основной источник правил. Русский BSL, '
    'локальный стиль отступов, сохранение BOM/окончаний строк, клиент/сервер и Экспорт. '
    'XML: сохранять UUID и связи метаданных. configuration/ — реализация; scripts/bsl — '
    'заготовки, которые нужно согласовывать для генерируемых участков. Старые генераторы '
    'могут перезаписать текущие исходники. После существенной правки обновить docs и нужную заметку.',
    'current_status': '# Статус\nСм. docs/status.md и docs/serena.md: там актуальные результаты '
    'проверок и ограничения MCP/BSL. Начальный Vanessa UI-набор — docs/vanessa.md; '
    'результаты — docs/status.md. Различать реализовано, запланировано и проверено. '
    'В новом чате явно активировать текущий абсолютный путь, прочитать initial_instructions '
    'и нужные заметки, проверить затрагиваемые символы. Не обещать .feature ↔ BSL-связи. '
    'Обновлять статус и эту заметку после существенных изменений.',
}


async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    config_path = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'config.toml'
    config = tomllib.loads(config_path.read_text(encoding='utf-8-sig'))['mcp_servers']['serena']
    project = yaml.safe_load((ROOT / '.serena/project.yml').read_text(encoding='utf-8'))
    assert project['language_servers'] == ['bsl']
    env = {**os.environ, **config.get('env', {})}
    params = StdioServerParameters(command=config['command'], args=config['args'], env=env)
    evidence = {'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'project': str(ROOT), 'calls': {}}
    with (OUT / 'server.log').open('w', encoding='utf-8') as log:
        async with stdio_client(params, errlog=log) as (read, write):
            async with ClientSession(read, write) as session:
                init = await session.initialize()
                evidence['initialize'] = init.model_dump(mode='json')
                listed = await session.list_tools()
                evidence['tools'] = [t.model_dump(mode='json') for t in listed.tools]
                print('Tools:', ', '.join(t.name for t in listed.tools), flush=True)

                async def call(name, args):
                    result = await session.call_tool(name, args)
                    data = result.model_dump(mode='json')
                    evidence['calls'].setdefault(name, []).append({'args': args, 'result': data})
                    (OUT / 'result.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding='utf-8')
                    print(name, json.dumps(data, ensure_ascii=False)[:2400], flush=True)
                    if result.isError:
                        raise RuntimeError(f'{name}: {data}')
                    return result

                await call('activate_project', {'project': str(ROOT)})
                await call('initial_instructions', {})
                def payload(result):
                    return json.loads(result.content[0].text)

                overview = payload(await call('get_symbols_overview', {'relative_path': MODULE, 'depth': 0}))
                assert 'ЗаблокироватьУчет' in overview.get('Method', []), overview
                symbols = payload(await call('find_symbol', {'name_path_pattern': 'ЗаблокироватьУчет', 'relative_path': MODULE, 'include_body': True}))
                assert symbols and 'Блокировка.Заблокировать();' in symbols[0]['body'], symbols
                references = payload(await call('find_referencing_symbols', {'name_path': 'ЗаблокироватьУчет', 'relative_path': MODULE}))
                assert any('Documents' in path for path in references), references
                evidence['summary'] = {
                    'tools': len(listed.tools),
                    'methods': len(overview.get('Method', [])),
                    'reference_files': len(references),
                    'referencing_symbols': sum(len(items) for groups in references.values() for items in groups.values()),
                }
                for name, body in MEMORIES.items():
                    await call('write_memory', {'memory_name': name, 'content': body})
                    readback = await call('read_memory', {'memory_name': name})
                    assert any(body in getattr(c, 'text', '') for c in readback.content), name
                await call('list_memories', {})
    print('MCP verification finished:', OUT / 'result.json', flush=True)


if __name__ == '__main__':
    asyncio.run(main())
