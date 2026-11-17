# ЛР 5. Рождение процесса

Система: macOS (Apple Silicon)
Программа записи: `sudo fs_usage`

## Рождение
Родитель: `bash`, PID 60529.
Новая программа: `hostname`.
Событие создания процесса: `posix_spawn`.

## Завершение
Код завершения у ребёнка и у родителя: 7.
Для `nosuch` система вывела `No such file or directory`; код завершения — 127.

## Запуск из Python
Python запустил `hostname` через `subprocess.run`, забрал вывод и получил код возврата 0.

## Снимки экрана

![1. Рождение процесса](screenshots/01_birth.png)
![2. Библиотеки нового процесса](screenshots/02_libraries.png)
![3. Код завершения 7](screenshots/03_exit_code.png)
![4. Программы нет](screenshots/04_no_program.png)
![5. Запуск из Python](screenshots/05_python_child.png)
