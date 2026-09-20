#!/usr/bin/env python3
"""Portable config snapshot and migration. No third party Python modules."""
import argparse, ast, datetime, hashlib, json, os, platform, re, shutil, subprocess, sys
from pathlib import Path
from urllib.parse import unquote
ROOT = Path(__file__).resolve().parent.parent
HOME = Path.home()
COMPONENTS = ['common','bash','zsh','oh-my-zsh','starship','vim','nvim','tex','rime','theme','fonts','windows-fonts','gtk4','grub','runtime']
DEPS = {'bash':['common','starship'], 'zsh':['common','oh-my-zsh'], 'tex':['common']}
def run(*args):
    return subprocess.run(args, check=True, text=True, stdout=subprocess.PIPE).stdout.strip()
def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
def exists(p): return p.exists() or p.is_symlink()
def remove(p):
    if p.is_symlink() or p.is_file(): p.unlink()
    elif p.exists(): shutil.rmtree(p)
def copy(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir() and not src.is_symlink(): shutil.copytree(src,dst,symlinks=True)
    else: shutil.copy2(src,dst,follow_symlinks=False)
def digest(p):
    if p.is_symlink(): return hashlib.sha256(('LINK:'+os.readlink(p)).encode()).hexdigest()
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def snapshot():
    if (ROOT/'manifest.json').exists(): raise RuntimeError('快照已存在；请在新目录制作新快照，避免覆盖原始包。')
    entries=[]; missing=[]
    def add(component, src, dest=None, scope='home'):
        src=Path(src)
        if not exists(src): missing.append(str(src)); return
        if dest is None: dest=str(src.relative_to(HOME)) if scope=='home' else str(src).lstrip('/')
        target=ROOT/'payload'/component/scope/dest
        target.parent.mkdir(parents=True,exist_ok=True)
        if src.is_dir() and not src.is_symlink():
            shutil.copytree(src,target,symlinks=True,ignore=shutil.ignore_patterns('__pycache__'))
        else: shutil.copy2(src,target,follow_symlinks=False)
        entries.append(dict(component=component,source=str(src),scope=scope,dest=dest,payload=str(target.relative_to(ROOT))))
        print(f'[打包] {component}: {src} → {target}',flush=True)
    specs={
      'common':['.config/shell/common','.config/shell/README.md'],
      'bash':['.bashrc','.bash_profile','.bash_login','.profile','.bash_logout','.bash_aliases','.inputrc','.blerc','.config/shell/bash','.local/share/blesh'],
      'zsh':['.zshrc','.zprofile','.zshenv','.zlogin','.zlogout','.p10k.zsh','.config/shell/zsh'],
      'oh-my-zsh':['.oh-my-zsh'], 'starship':['.config/starship.toml'],
      'vim':['.vimrc','.vim/config','.vim/autoload','.vim/plugged','.vim/coc-settings.json','Templates','.config/coc','.config/EDITORS.md','.config/vim-templates.md'],
      'nvim':['.config/nvim','.local/share/nvim/lazy','.local/share/nvim/language.txt'],
      'tex':['.config/shell/tex','.latexrc'],
      'rime':['.local/share/fcitx5/rime','.config/fcitx5','.config/environment.d/fcitx.conf','.config/autostart/org.fcitx.Fcitx5.desktop','.xinputrc'],
      'theme':['.themes','.local/share/icons','.config/gtk-3.0'],
      'gtk4':['.config/gtk-4.0'],
      'fonts':['.local/share/fonts','.fonts','.config/fontconfig'],
      'runtime':['.local/share/nvim/mason','.local/share/nvim/site','.local/share/editor-python'],
    }
    for comp, paths in specs.items():
        for rel in paths: add(comp,HOME/rel)
    for p in ['/etc/default/grub','/etc/default/grub.d','/etc/grub.d','/boot/grub/themes']:
        add('grub',p,scope='system')
    add('theme','/usr/share/icons/whiteglass',scope='system')
    # Fonts selected by GNOME are installed in the system on Ubuntu; retain exact origin.
    add('fonts','/usr/share/fonts/truetype/ubuntu',scope='system')
    settings=[]
    schemas=run('gsettings','list-schemas').splitlines()
    selected={
      'org.gnome.desktop.interface':['gtk-theme','icon-theme','cursor-theme','cursor-size','color-scheme','accent-color','font-name','document-font-name','monospace-font-name','text-scaling-factor','font-antialiasing','font-hinting','font-rgba-order'],
      'org.gnome.desktop.wm.preferences':['theme','titlebar-font','button-layout'],
      'org.gnome.desktop.background':None,'org.gnome.desktop.screensaver':['picture-uri','picture-options','primary-color','secondary-color'],
      'org.gnome.shell.extensions.user-theme':['name']}
    for schema,keys in selected.items():
        if schema not in schemas: continue
        available=run('gsettings','list-keys',schema).splitlines()
        for key in keys or available:
            if key not in available: continue
            value=run('gsettings','get',schema,key)
            settings.append([schema,key,value])
            if key.startswith('picture-uri'):
                uri=ast.literal_eval(value)
                if uri.startswith('file://'):
                    p=Path(unquote(uri[7:])); scope='home' if p.is_relative_to(HOME) else 'system'
                    if not any(e['source']==str(p) for e in entries): add('theme',p,scope=scope)
    dump(ROOT/'gnome-settings.json',settings)
    dump(ROOT/'manifest.json',dict(source_home=str(HOME),created=datetime.datetime.now().isoformat(),architecture=platform.machine(),os_release=Path('/etc/os-release').read_text(),entries=entries,missing_optional=missing))
    seal()
def seal():
    sums={}
    for name in ['payload','scripts','tests']:
        for p in sorted((ROOT/name).rglob('*')):
            if p.is_symlink() or p.is_file(): sums[str(p.relative_to(ROOT))]=digest(p)
    for name in ['manifest.json','gnome-settings.json','Makefile','README.md','FONT-INVENTORY.tsv','RIME-SNAPSHOT.json','VALIDATION.md']:
        p=ROOT/name
        if p.exists(): sums[name]=digest(p)
    dump(ROOT/'checksums.json',sums)
    print(f'[成功] 已记录 {len(sums)} 个文件/符号链接的 SHA256')
def verify():
    sums=json.loads((ROOT/'checksums.json').read_text()); errors=[]
    for rel,expected in sums.items():
        p=ROOT/rel
        if not exists(p) or digest(p)!=expected: errors.append(rel)
    if errors: raise RuntimeError('校验失败：'+repr(errors[:30]))
    print(f'[成功] SHA256 校验通过：{len(sums)} 个文件/链接')
def expand(component):
    if component=='all': return [c for c in COMPONENTS if c not in ['grub','runtime','gtk4','windows-fonts']]
    if component not in COMPONENTS: raise RuntimeError('未知组件 '+component)
    return list(dict.fromkeys(DEPS.get(component,[])+[component]))
def relocate(tree, old, new):
    paths=[tree] if not tree.is_dir() or tree.is_symlink() else list(tree.rglob('*'))
    for p in paths:
        if p.is_symlink():
            target=os.readlink(p)
            if old in target: p.unlink(); p.symlink_to(target.replace(old,new))
        elif p.is_file() and p.stat().st_size < 4*1024*1024:
            raw=p.read_bytes()
            if old.encode() in raw and b'\0' not in raw:
                try: text=raw.decode('utf-8')
                except UnicodeDecodeError: continue
                p.write_text(text.replace(old,new))
def apply(args):
    manifest=json.loads((ROOT/'manifest.json').read_text())
    comps=expand(args.component)
    if 'grub' in comps: raise RuntimeError('GRUB 使用 make grub-plan / make grub-apply；原文件仅作存档。')
    if 'runtime' in comps: raise RuntimeError('runtime 是机器相关二进制快照；新系统请 make editor-runtime 重建。')
    target=Path(args.target_home).absolute() if args.target_home else HOME
    if args.execute and os.geteuid()==0: raise RuntimeError('请以桌面普通用户运行；需要系统写入时脚本会调用 sudo。')
    entries=[e for e in manifest['entries'] if e['component'] in comps]
    if args.component=='windows-fonts':
        e=next(e.copy() for e in manifest['entries'] if e['component']=='fonts' and e['dest']=='.local/share/fonts')
        e.update(component='windows-fonts',source=e['source']+'/Microsoft',dest=e['dest']+'/Microsoft',payload=e['payload']+'/Microsoft')
        entries=[e]
    # Avoid overwriting an active LevelDB database.
    if args.execute and 'rime' in comps and subprocess.run(['pgrep','-u',str(os.getuid()),'-x','fcitx5'],stdout=subprocess.DEVNULL).returncode==0:
        raise RuntimeError('Fcitx5 正在运行。请先退出输入法，再执行迁移，防止用户词库被锁定。')
    system=[e for e in entries if e['scope']=='system']
    if args.execute and system and target!=HOME: raise RuntimeError('替代 HOME 只允许用户文件；测试请选 bash/zsh/vim/nvim/tex 等组件。')
    if args.execute:
        verify()
        if system: subprocess.run(['sudo','-v'],check=True)
    stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    backup=target/'.local/state/gnome-migrate'/stamp
    log=[]
    def save(): dump(backup/'restore.json',log)
    for e in entries:
        src=ROOT/e['payload']; dst=target/e['dest'] if e['scope']=='home' else Path('/')/e['dest']
        print(f'[{"复制" if args.execute else "预览"}] {e["component"]}: {src} → {dst}',flush=True)
        if not args.execute: continue
        saved=backup/'files'/str(len(log))
        record=dict(dest=str(dst),backup=str(saved),existed=exists(dst),system=e['scope']=='system')
        if record['system']:
            saved.parent.mkdir(parents=True,exist_ok=True)
            if exists(dst): subprocess.run(['sudo','cp','-a','--',str(dst),str(saved)],check=True)
            log.append(record); save()
            # System resource directories are dedicated theme/font directories.
            subprocess.run(['sudo','rm','-rf','--',str(dst)],check=True)
            subprocess.run(['sudo','mkdir','-p','--',str(dst.parent)],check=True)
            subprocess.run(['sudo','cp','-a','--',str(src),str(dst)],check=True)
            subprocess.run(['sudo','chown','-R','root:root',str(dst)],check=True)
        else:
            # Do not follow parent symlinks into locations outside requested HOME.
            if not dst.parent.resolve().is_relative_to(target.resolve()): raise RuntimeError('目标父目录链接超出 HOME: '+str(dst))
            if exists(dst): copy(dst,saved)
            log.append(record); save()
            staged=backup/'stage'/str(len(log)); copy(src,staged)
            relocate(staged,manifest['source_home'],str(target))
            if e['component']=='rime' and dst.name=='rime':
                remove(staged/'build') # rebuild with target librime ABI
                for lock in staged.glob('*.userdb/LOCK'): lock.unlink()
            remove(dst); dst.parent.mkdir(parents=True,exist_ok=True); shutil.move(str(staged),str(dst))
        print(f'[成功] {dst}；原内容备份：{saved if record["existed"] else "原路径不存在（已记录）"}',flush=True)
    if args.execute:
        print(f'[成功] 文件迁移完成。恢复索引：{backup}/restore.json')
        if any(c in comps for c in ['fonts','windows-fonts']) and shutil.which('fc-cache'): subprocess.run(['fc-cache','-f'],check=True)
        if 'theme' in comps: print('[待操作] make theme-settings 应用 GNOME 设置（需桌面会话）；make gtk4-apply 单独应用 GTK4 覆盖。')
        if 'rime' in comps: print('[待操作] 注销再登录，启动 Fcitx5 并执行“重新部署”；Debian/Ubuntu 可运行 im-config -n fcitx5。')
    else: print('[预览结束] 没有改动。添加 DO=1 执行；GTK4 覆盖另用 make gtk4-apply。')
def settings(execute):
    schemas=run('gsettings','list-schemas').splitlines(); previous=[]; skipped=[]; path=None
    if execute: verify()
    if execute and not os.environ.get('DBUS_SESSION_BUS_ADDRESS'): raise RuntimeError('请在目标用户 GNOME 桌面的终端运行。')
    for schema,key,value in json.loads((ROOT/'gnome-settings.json').read_text()):
        if schema not in schemas or key not in run('gsettings','list-keys',schema).splitlines():
            skipped.append(f'{schema} {key}'); continue
        value=value.replace(json.loads((ROOT/'manifest.json').read_text())['source_home'],str(HOME))
        print(f'[{"设置" if execute else "预览"}] {schema} {key} = {value}')
        if execute:
            previous.append([schema,key,run('gsettings','get',schema,key)])
            path=HOME/'.local/state/gnome-migrate'/('settings-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'.json') if len(previous)==1 else path
            dump(path,previous)
            subprocess.run(['gsettings','set',schema,key,value],check=True)
    if execute: print('[完成] GNOME 设置写入 '+str(len(previous))+' 项；原值备份：'+str(path))
    for item in skipped: print('[跳过：目标 GNOME 不支持] '+item)
def restore(args):
    records=json.loads(Path(args.backup).read_text())
    for r in reversed(records):
        dst=Path(r['dest']); src=Path(r['backup'])
        print(f'[{"恢复" if args.execute else "恢复预览"}] {src} → {dst}; 原先存在={r["existed"]}')
        if not args.execute: continue
        if r['system']:
            subprocess.run(['sudo','rm','-rf','--',str(dst)],check=True)
            if r['existed']: subprocess.run(['sudo','cp','-a','--',str(src),str(dst)],check=True)
        else:
            remove(dst)
            if r['existed']: copy(src,dst)
def main():
    p=argparse.ArgumentParser(); p.add_argument('action',choices=['snapshot','seal','verify','apply','settings','restore','settings-restore']); p.add_argument('component',nargs='?',default='all'); p.add_argument('--execute',action='store_true'); p.add_argument('--target-home'); p.add_argument('--backup'); a=p.parse_args()
    if a.action=='snapshot': snapshot()
    elif a.action=='seal': seal()
    elif a.action=='verify': verify()
    elif a.action=='apply': apply(a)
    elif a.action=='settings': settings(a.execute)
    elif a.action=='restore': restore(a)
    elif a.action=='settings-restore':
        for schema,key,value in json.loads(Path(a.backup).read_text()):
            print('[恢复设置]',schema,key,value)
            if a.execute: subprocess.run(['gsettings','set',schema,key,value],check=True)
if __name__=='__main__':
    try: main()
    except (RuntimeError,OSError,subprocess.CalledProcessError,ValueError) as e:
        print('[失败] '+str(e),file=sys.stderr); sys.exit(1)
