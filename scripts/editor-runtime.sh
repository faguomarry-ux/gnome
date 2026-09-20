#!/bin/sh
set -eu
export PATH="$HOME/.local/bin:$PATH"
[ "${DO:-0}" = 1 ] || { echo '[预览] 建立 ~/.local/share/editor-python；pip 安装 pynvim/debugpy；Lazy restore 根据锁文件还原插件；等待并安装记录中的 14 个 Mason 工具。'; exit 0; }
[ "$(id -u)" -ne 0 ] || { echo '[失败] 请使用普通用户'; exit 1; }
nvim --clean --headless '+lua if vim.fn.has("nvim-0.11.2")==0 then vim.cmd("cquit 1") end' +qa
if [ ! -e "$HOME/.local/share/editor-python" ]; then
 python3 -m venv "$HOME/.local/share/editor-python"
fi
"$HOME/.local/share/editor-python/bin/python" -m pip install pynvim debugpy virtualenv
export PATH="$HOME/.local/bin:$PATH"
nvim --headless '+Lazy! restore' '+Lazy! build' +qa
ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
export GNOME_MIGRATE_ROOT="$ROOT_DIR"
nvim --headless -u NONE -l "$ROOT_DIR/scripts/mason-restore.lua"
echo '[成功] Python provider、插件和源机器的 Mason 工具安装完成；语言解析器在首次使用时按配置编译。'
