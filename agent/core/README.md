# Ядро агента (C)

Первая функция ядра — `core_get_info`. Она заполняет `core_info` сведениями о системе, включая время работы без перезагрузки (`uptime_s`), и возвращает код ошибки.

- `core.h` — описание структуры и функции.
- `core_info.c` — реализация для macOS/Linux и Windows.
- `show_info.c` — небольшая программа для ручного вызова ядра.

После задания модуля 1 структура занимает 280 байт; на macOS `uptime_s` вычисляется по `kern.boottime`, на Linux через `sysinfo`, в Windows через `GetTickCount64`.

На macOS проверьте ядро и соберите библиотеку:

```sh
clang -Wall -Wextra -o show_info show_info.c core_info.c && ./show_info
clang -Wall -Wextra -shared -fPIC -o libsentry_core.dylib core_info.c
nm -gU libsentry_core.dylib
```

Собранная библиотека не коммитится: она создаётся из исходников на компьютере пользователя.
