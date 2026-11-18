from pathlib import Path
import shutil,sys,time
base=Path(__file__).parent;inbox=base/'inbox';src=base/'source'
inbox.mkdir(exist_ok=True)
mode=sys.argv[1] if len(sys.argv)>1 else 'slow'
if mode=='slow':
    target=inbox/'bulk_payload.bin'
    with (src/'bulk_payload.bin').open('rb') as r,target.open('wb') as w:
        while chunk:=r.read(65536):
            w.write(chunk);w.flush();time.sleep(0.35)
    print('Файл загружен полностью')
elif mode=='duplicate':
    shutil.copy2(src/'order_000.txt',inbox/'заказ.txt')
    time.sleep(1)
    shutil.copy2(src/'order_001.txt',inbox/'заказ.txt')
    print('Файл с тем же именем перезаписан другим содержимым')
elif mode=='broken':
    (inbox/'incomplete.txt').write_bytes((src/'order_003.txt').read_bytes()[:35])
    print('Создан неполный файл')
elif mode=='burst':
    for p in sorted(src.glob('order_*.txt')):shutil.copy2(p,inbox/p.name)
    print('Создано 15 файлов')
else:sys.exit('Укажите slow, duplicate, broken или burst')
