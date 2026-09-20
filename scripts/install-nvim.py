#!/usr/bin/env python3
import hashlib,os,platform,shutil,subprocess,tarfile,tempfile,urllib.request
from pathlib import Path
version='v0.11.6'
assets={'x86_64':('x86_64','2fc90b962327f73a78afbfb8203fd19db8db9cdf4ee5e2bef84704339add89cc'),'aarch64':('arm64','8ddc0c101846145e830b17bbca50782ca9307eee4fab539d9e2ddaf8793c06f1')}
if platform.machine() not in assets: raise SystemExit('[失败] 官方预编译包只支持 x86_64/aarch64；此架构请从发行版安装 Neovim >= 0.11.2')
arch,sha=assets[platform.machine()]; name='nvim-linux-'+arch
url=f'https://github.com/neovim/neovim/releases/download/{version}/{name}.tar.gz'
dest=Path.home()/'.local/opt'/('nvim-'+version); link=Path.home()/'.local/bin/nvim'
print('[安装方案]',url,'→',dest,'；命令入口 →',link)
if os.environ.get('DO')!='1': raise SystemExit(0)
if dest.exists() or link.exists() or link.is_symlink(): raise SystemExit('[失败] 用户级 Neovim 路径已存在；请先检查/备份后重试：'+str(dest)+' / '+str(link))
with tempfile.TemporaryDirectory() as td:
    archive=Path(td)/'nvim.tar.gz'
    urllib.request.urlretrieve(url,archive)
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=sha: raise SystemExit('[失败] Neovim 官方包 SHA256 不匹配')
    with tarfile.open(archive) as tar: tar.extractall(td,filter='data')
    subprocess.run([str(Path(td)/name/'bin/nvim'),'--version'],check=True,stdout=subprocess.DEVNULL)
    dest.parent.mkdir(parents=True,exist_ok=True);shutil.move(str(Path(td)/name),dest)
    link.parent.mkdir(parents=True,exist_ok=True);link.symlink_to(dest/'bin/nvim')
print('[成功] Neovim',version,'已安装并校验；新终端使用 ~/.local/bin/nvim。')
