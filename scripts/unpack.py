#!/usr/bin/env python3
"""Verify ordered GitHub volumes and restore the payload without changing HOME."""
import hashlib,json,os,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent

def main():
    if (ROOT/'payload').exists():
        print('[检查] payload 已存在；不覆盖，改为校验现有迁移包。',flush=True)
        subprocess.run(['python3',str(ROOT/'scripts/migrate.py'),'verify'],check=True)
        return
    meta=json.loads((ROOT/'transfer/parts.json').read_text())
    (ROOT/'dist').mkdir(exist_ok=True)
    archive=ROOT/'dist'/meta['archive']
    pending=archive.with_suffix(archive.suffix+'.assembling')
    total=0; full=hashlib.sha256()
    try:
        with pending.open('wb') as out:
            for index,part in enumerate(meta['parts'],1):
                name=part['name']
                if Path(name).name!=name: raise RuntimeError('非法分卷名称')
                p=ROOT/'transfer'/name; h=hashlib.sha256();size=0
                with p.open('rb') as f:
                    for chunk in iter(lambda:f.read(1024*1024),b''):
                        h.update(chunk);full.update(chunk);size+=len(chunk);out.write(chunk)
                if size!=part['bytes'] or h.hexdigest()!=part['sha256']: raise RuntimeError('分卷校验失败：'+name)
                total+=size;print(f'[成功] 校验分卷 {index}/{len(meta["parts"])}：{name}',flush=True)
        if total!=meta['archive_bytes'] or full.hexdigest()!=meta['archive_sha256']:raise RuntimeError('完整压缩包校验失败')
        pending.replace(archive)
        with tempfile.TemporaryDirectory(prefix='.unpack-',dir=ROOT) as stage:
            print('[解压] 仅恢复 payload 资源；保留仓库中的新版脚本与文档。',flush=True)
            subprocess.run(['tar','-xzf',str(archive),'-C',stage,'./payload'],check=True)
            shutil.move(str(Path(stage)/'payload'),str(ROOT/'payload'))
        print('[成功] 资源已恢复到 '+str(ROOT/'payload'),flush=True)
        subprocess.run(['python3',str(ROOT/'scripts/migrate.py'),'verify'],check=True)
    finally:
        if pending.exists(): pending.unlink()
if __name__=='__main__':main()
