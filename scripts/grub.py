#!/usr/bin/env python3
"""Merge portable visual GRUB settings without copying machine boot configuration."""
import datetime, os, re, shutil, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
execute='--execute' in sys.argv
release=Path('/etc/os-release').read_text()
if re.search(r'^ID=(?:"?)(fedora|rhel|centos|rocky|almalinux)',release,re.M):
    command=['grub2-mkconfig','-o','/boot/grub2/grub.cfg']; themes=Path('/boot/grub2/themes')
elif shutil.which('update-grub'):
    command=['update-grub']; themes=Path('/boot/grub/themes')
elif shutil.which('grub2-mkconfig') and Path('/boot/grub2').is_dir():
    command=['grub2-mkconfig','-o','/boot/grub2/grub.cfg']; themes=Path('/boot/grub2/themes')
elif shutil.which('grub-mkconfig') and Path('/boot/grub').is_dir():
    command=['grub-mkconfig','-o','/boot/grub/grub.cfg']; themes=Path('/boot/grub/themes')
else: sys.exit('[失败] 无法识别目标 GRUB；未执行任何写入。')
source=ROOT/'payload/grub/system/boot/grub/themes/whitesur'
if not (source/'theme.txt').exists(): sys.exit('[失败] 缺少 WhiteSur GRUB 主题')
# Keep target's GRUB_DEFAULT, CMDLINE, UUID, BLS and distribution settings.
values={'GRUB_THEME':'"'+str(themes/'whitesur/theme.txt')+'"','GRUB_GFXMODE':'2560x1440,auto','GRUB_TIMEOUT_STYLE':'menu','GRUB_TIMEOUT':'5'}
if '--original-timeout' in sys.argv: values.update(GRUB_TIMEOUT_STYLE='hidden',GRUB_TIMEOUT='0')
original=Path('/etc/default/grub').read_text(); updated=original
for key,value in values.items():
    updated=re.sub(r'^\s*'+key+r'=.*\n?', '',updated,flags=re.M)
    updated+='\n'+key+'='+value+'\n'
print('[方案] 仅迁移外观；保留目标内核参数、默认启动项、UUID、BLS。')
for k,v in values.items(): print(k+'='+v)
print('[复制]',source,'→',themes/'whitesur')
print('[重建] sudo '+' '.join(command))
if execute:
    if os.geteuid()==0: sys.exit('[失败] 请普通用户运行，由脚本调用 sudo。')
    subprocess.run([sys.executable,str(ROOT/'scripts/migrate.py'),'verify'],check=True)
    subprocess.run(['sudo','-v'],check=True)
    stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    backup=Path('/var/backups/gnome-migrate')/stamp
    subprocess.run(['sudo','mkdir','-p',str(backup)],check=True)
    subprocess.run(['sudo','cp','-a','/etc/default/grub',str(backup/'grub')],check=True)
    cfg=Path(command[-1]) if command[0]!='update-grub' else Path('/boot/grub/grub.cfg')
    if cfg.exists(): subprocess.run(['sudo','cp','-a',str(cfg),str(backup/'grub.cfg')],check=True)
    dest=themes/'whitesur'
    if dest.exists(): subprocess.run(['sudo','cp','-a',str(dest),str(backup/'whitesur')],check=True)
    import tempfile
    with tempfile.TemporaryDirectory() as temp:
        candidate=Path(temp)/'grub'; candidate.write_text(updated)
        subprocess.run(['sh','-n',str(candidate)],check=True)
        subprocess.run(['sudo','mkdir','-p',str(themes)],check=True)
        subprocess.run(['sudo','rm','-rf','--',str(dest)],check=True)
        subprocess.run(['sudo','cp','-a',str(source),str(dest)],check=True)
        subprocess.run(['sudo','chown','-R','root:root',str(dest)],check=True)
        subprocess.run(['sudo','install','-m','644',str(candidate),'/etc/default/grub'],check=True)
        print('[备份]',backup,flush=True)
        result=subprocess.run(['sudo']+command)
        if result.returncode:
            subprocess.run(['sudo','cp','-a',str(backup/'grub'),'/etc/default/grub'],check=True)
            if (backup/'grub.cfg').exists(): subprocess.run(['sudo','cp','-a',str(backup/'grub.cfg'),str(cfg)],check=True)
            sys.exit('[失败] GRUB 生成失败，已回滚配置；备份：'+str(backup))
    print('[成功] GRUB 外观已迁移；备份：',backup)
else: print('[预览结束] 执行用 make grub-apply DO=1；不会调用 grub-install 或改写 EFI stub。')
