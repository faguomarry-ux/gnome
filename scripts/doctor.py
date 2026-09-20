#!/usr/bin/env python3
import json,os,platform,shutil,subprocess
from pathlib import Path
root=Path(__file__).resolve().parent.parent
m=json.loads((root/'manifest.json').read_text())
print('当前系统:',platform.platform())
print('源 HOME:',m['source_home'],'→ 当前 HOME:',Path.home())
print('源架构:',m['architecture'],'→ 当前架构:',platform.machine())
for cmd in ['bash','zsh','vim','nvim','starship','fcitx5','rime_deployer','node','npm','gcc','make','latexmk','biber','xelatex','fc-cache']:
    print('[已安装]' if shutil.which(cmd) else '[缺少]',cmd,shutil.which(cmd) or '')
if shutil.which('nvim'): print('[Neovim]', subprocess.run(['nvim','--version'],stdout=subprocess.PIPE,text=True).stdout.splitlines()[0])
print('[Oh My Zsh]',(Path.home()/'.oh-my-zsh/oh-my-zsh.sh').exists())
print('[GNOME 会话]',os.environ.get('XDG_CURRENT_DESKTOP','未设置'))
print('[提示] runtime 仅存档，Mason/venv/Treesitter 二进制在新系统重建。')
print('[提示] tex 配置包含 TeX Live 2026 路径；系统 TeX 可由 PATH 回退使用，完整版需 make install-tex DO=1。')
print('[提示] GSettings 逐项检测，旧 GNOME 无 accent-color 等键时报告跳过；扩展不盲目启用。')
print('[提示] 主题不会自动应用到 Flatpak 沙盒；GTK4 CSS 需单独迁移并在目标版本验证。')
