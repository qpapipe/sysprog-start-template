# Мозг агента (Python)

`brain.py` загружает библиотеку ядра через `ctypes`, описывает структуру `CoreInfo` и вызывает `core_get_info`. При запуске без параметров печатает событие `agent_started` в JSON.

На macOS из корня репозитория:

```sh
clang -Wall -Wextra -shared -fPIC -o agent/core/libsentry_core.dylib agent/core/core_info.c
python3 agent/brain/brain.py
```

Для отправки JSON в вебхук n8n передайте его URL аргументом:

```sh
python3 agent/brain/brain.py http://localhost:5678/webhook-test/agent
```

Сценарий n8n хранится в `agent/n8n/agent-started.json`; данные подключений и секреты в репозиторий не добавляются.
