# Локальная Serena для Codex

## Установка 26.11.2026
- Официальный репозиторий: https://github.com/oraios/serena.
- Установлен релиз **v1.7.0**, commit `949a27ef1e5fda1a6e7b561e777bcece345c6ffd`,
  отдельный checkout вне репозитория проекта (detached HEAD).
  Его каталог выбирается локально; в этом документе обозначен как `<SERENA_DIR>`.
  Зависимости установлены `uv sync --frozen --no-dev --python 3.11` по lock-файлу;
  Python 3.11.15, MCP SDK 1.28.1. Не обновлять checkout незаметно: после обновления
  повторить MCP- и BSL-проверки.
- Причина фиксации релиза: main `23c06ff715409b2e9dc9be7ca26b7b2fbf356b7c`
  (2.1.1.dev0 / MCP SDK 2.2.0) запустился и отдал tools/list, но `activate_project`
  вернул ошибку валидации `session: Field required`. Исходники Serena не патчились.
- BSL/OneScript обслуживает штатный для v1.7.0 **bsl-language-server 0.29.0**
  от 1c-syntax; загрузчик проверяет SHA-256
  `d6fa9ad638ba51855e260b88ad1f8ce4e602385845a4ee43600d148f779bcf0b`.
  Выбор версии соответствует установленному коду; актуальная документация main
  может описывать более новую версию LSP.
- Для этой версии требуется **Java 21+** (проверено по адаптеру выбранного релиза).
  Temurin JRE 21.0.13.1 установлена из официального Adoptium ZIP с проверкой SHA-256
  в отдельный локальный каталог, далее `<JAVA_HOME_SERENA>`.
  Системная Java 8 и глобальные переменные окружения не изменялись.

## Подключение
Пользовательский конфиг — `config.toml` в каталоге `CODEX_HOME`, по умолчанию
`~/.codex/config.toml`. Добавлена секция `mcp_servers.serena`, stdio.
`command` содержит реальный абсолютный путь к исполняемому файлу Serena:
на Windows это `<SERENA_DIR>\.venv\Scripts\serena.exe` при установке через `uv sync`.
`<SERENA_DIR>` и `<JAVA_HOME_SERENA>` — обозначения для документации: перед записью
в конфиг их нужно заменить фактическими абсолютными путями данного компьютера.
Аргументы: `start-mcp-server --context codex --enable-web-dashboard false --enable-gui-log-window false`.
Таймаут старта 120 с, инструментов 180 с. `JAVA_HOME` и PATH с Java 21 заданы
только в окружении MCP-сервера; PATH записан полностью (TOML не интерполирует `$PATH`).
При переносе установки пересоздать эти абсолютные пути и PATH для нового компьютера.

Глобальная запись **не содержит** `--project`, `cwd` или пути к ферме; другие проекты
активируются обычным `activate_project`. Существующие настройки и `node_repl` сохранены.
Резервная копия до изменения сохранена рядом с конфигом под именем
`config.toml.bak-serena-<дата-время>`. Пользовательский конфиг и его копии
остаются локальными, в репозиторий проекта их не добавлять.
В старом `~/.serena/serena_config.yml` уже была регистрация другого проекта;
Serena добавляет текущий проект при активации, не подменяя остальные.
Сетевые облачные сервисы и API-ключи не подключались; MCP работает локально.

Проектная конфигурация — `.serena/project.yml`: язык `bsl`, workspace `configuration/`,
gitignore и дополнительные исключения для баз, артефактов и зависимостей.
Python-скрипты и Markdown доступны текстовым поиском, отдельный Python LSP не настроен.
`.bsl` и `.os` поддерживаются адаптером, но `.os`-файлов в этом проекте нет и
работа OneScript runtime не проверялась. Память и project.yml сохраняются в Git;
кеши/логи `.serena` и протокол диагностики `.build` исключены.

## Повторная проверка
Из корня в PowerShell сначала посмотрите фактическую настройку:

```powershell
codex mcp get serena
```

Для установки через `uv sync` найдите Python рядом с `serena.exe` из поля
`command`: `<SERENA_DIR>\.venv\Scripts\python.exe`. Скопируйте его реальный
абсолютный путь в переменную и запустите диагностику:

```powershell
$serenaPython = Read-Host 'Абсолютный путь к Python окружения Serena'
if (-not (Test-Path -LiteralPath $serenaPython -PathType Leaf)) {
    throw 'Python окружения Serena не найден'
}
& $serenaPython scripts/check_serena.py
```

Для другого способа установки используйте Python с зависимостями MCP и PyYAML.
Клонирование проекта само по себе не устанавливает Serena и Java. На новом
компьютере их нужно установить, настроить локальный MCP и повторить проверку.

Диагностика использует именно команду/окружение из config.toml и MCP SDK,
запрашивает initialize и tools/list, активирует проект, читает символы настоящего
модуля, ищет использования, создаёт и перечитывает тематическую память.
Это не запуск 1С; изменяются только заметки и `.build/serena-check/`.
Машинный протокол: `.build/serena-check/result.json`, stderr: `server.log` рядом.
Итог и ограничения — в [статусе](status.md).

## Новый чат
Перезапустить Codex для перечитывания пользовательского MCP-конфига, открыть чат
в текущем репозитории. AGENTS.md подхватывается как проектная инструкция.
Попросить активировать **абсолютный текущий путь**, прочитать `initial_instructions`,
`list_memories` и нужные `read_memory`, затем docs/status.md и затрагиваемый код.
Текущий корень определять через `git rev-parse --show-toplevel`, а не брать из
примера или памяти другого компьютера. Проектные пути в документации заданы
относительно этого корня; рабочие абсолютные пути остаются в локальном MCP-конфиге.
Если Serena отсутствует в инструментах, проверить раздел MCP в настройках и
`codex mcp get serena`; не считать внешний диагностический прогон подтверждением
подключения к уже открытому чату.

Основные заметки: `project_overview`, `commands_and_testing`, `conventions`,
`current_status`. Они ссылаются на документы, не заменяют их. После существенных
изменений обновлять основной документ и соответствующую заметку. Семантическая
связь Vanessa `.feature` ↔ BSL не проверена.

## Официальные источники
- [Serena: установка](https://oraios.github.io/serena/02-usage/010_installation.html),
  [Codex-клиент](https://oraios.github.io/serena/02-usage/030_clients.html#codex-cli-and-via-chatgpt-app),
  [конфигурация](https://oraios.github.io/serena/02-usage/050_configuration.html).
- [Адаптер BSL выбранного релиза](https://github.com/oraios/serena/blob/v1.7.0/src/solidlsp/language_servers/bsl_language_server.py).
- [OpenAI: MCP в Codex](https://learn.chatgpt.com/docs/extend/mcp).
