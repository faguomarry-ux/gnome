#!/bin/sh
# POSIX sh: supports Debian/Ubuntu, Fedora/RHEL family, Arch and openSUSE.
set -eu
ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
ACTION=${1:-all}
DO=${DO:-0}
export PATH="$HOME/.local/bin:$PATH"
[ "$(id -u)" -ne 0 ] || { echo '[失败] 请用普通桌面用户运行；仅包管理器通过 sudo 提权。' >&2; exit 1; }
. /etc/os-release
case " ${ID:-} ${ID_LIKE:-} " in
 *debian*|*ubuntu*) PM=apt ;;
 *fedora*|*rhel*|*centos*) PM=dnf ;;
 *arch*) PM=pacman ;;
 *suse*) PM=zypper ;;
 *) echo "[失败] 未支持的包管理器: ${ID:-unknown}" >&2; exit 1 ;;
esac
if [ -e /run/ostree-booted ]; then
 echo '[失败] 检测到 Atomic/Silverblue；请先通过 rpm-ostree 分层安装依赖并重启。当前安装脚本面向可变系统。' >&2; exit 1
fi
execute() {
 printf '[%s]' "$( [ "$DO" = 1 ] && echo 执行 || echo 预览 )"
 printf ' <%s>' "$@"; printf '\n'
 [ "$DO" != 1 ] || "$@"
}
packages() {
 case "$PM" in
 apt) execute sudo apt-get update; execute sudo apt-get install -y "$@" ;;
 dnf) execute sudo dnf install -y "$@" ;;
 pacman) execute sudo pacman -S --needed "$@" ;;
 zypper) execute sudo zypper --non-interactive install "$@" ;;
 esac
}
ensure() {
 binary=$1; package=$2
 if [ "$PM" = pacman ] && [ "$package" = python3 ]; then package=python; fi
 if command -v "$binary" >/dev/null 2>&1; then printf '[已安装] %s → %s\n' "$binary" "$(command -v "$binary")"
 else packages "$package"; fi
}
omz() {
 ensure git git
 if [ -f "$HOME/.oh-my-zsh/oh-my-zsh.sh" ]; then echo "[已安装] Oh My Zsh → $HOME/.oh-my-zsh"
 elif [ -d "$ROOT_DIR/payload/oh-my-zsh/home/.oh-my-zsh" ]; then
   if [ -e "$HOME/.oh-my-zsh" ]; then echo '[失败] .oh-my-zsh 已存在但不完整；请先 make apply-oh-my-zsh DO=1（带备份）。' >&2; exit 1; fi
   execute cp -a "$ROOT_DIR/payload/oh-my-zsh/home/.oh-my-zsh" "$HOME/.oh-my-zsh"
 else execute git clone --depth=1 https://github.com/ohmyzsh/ohmyzsh.git "$HOME/.oh-my-zsh"; fi
}
starship_install() {
 if command -v starship >/dev/null 2>&1; then echo "[已安装] Starship → $(command -v starship)"; return; fi
 ensure curl curl
 if [ "$DO" != 1 ]; then echo '[预览] 从 https://starship.rs/install.sh 下载官方安装脚本，安装到 ~/.local/bin/starship'; return; fi
 tmp_dir=$(mktemp -d); trap 'rm -rf "$tmp_dir"' EXIT HUP INT TERM
 curl --fail --location --proto '=https' --tlsv1.2 https://starship.rs/install.sh -o "$tmp_dir/starship-install.sh"
 mkdir -p "$HOME/.local/bin"
 sh "$tmp_dir/starship-install.sh" --yes --bin-dir "$HOME/.local/bin"
 "$HOME/.local/bin/starship" --version
}
case "$ACTION" in
 all)
  for pair in 'bash bash' 'zsh zsh' 'vim vim' 'nvim neovim' 'git git' 'curl curl' 'make make' 'python3 python3'; do
    # All entries above are constant package identifiers.
    set -- $pair; ensure "$1" "$2"
  done
  omz; starship_install ;;
 bash|zsh|vim) ensure "$ACTION" "$ACTION" ;;
 nvim) ensure nvim neovim ;;
 oh-my-zsh) omz ;;
 starship) starship_install ;;
 rime)
  case "$PM" in
   apt) packages fcitx5 fcitx5-rime librime-plugin-lua fcitx5-chinese-addons fcitx5-frontend-gtk3 fcitx5-frontend-gtk4 fcitx5-frontend-qt5 fcitx5-config-qt im-config ;;
   dnf) packages fcitx5 fcitx5-rime librime-lua fcitx5-chinese-addons fcitx5-gtk fcitx5-qt fcitx5-configtool ;;
   pacman) packages fcitx5 fcitx5-rime fcitx5-chinese-addons fcitx5-gtk fcitx5-qt fcitx5-configtool ;;
   zypper) packages fcitx5 fcitx5-rime fcitx5-gtk fcitx5-qt fcitx5-configtool ;;
  esac ;;
 theme) packages gnome-tweaks ;;
 editor-deps)
  case "$PM" in
   apt) packages build-essential python3-venv python3-dev nodejs npm ripgrep fd-find fzf unzip curl git ;;
   dnf) packages gcc gcc-c++ make python3-devel nodejs npm ripgrep fd-find fzf unzip curl git ;;
   pacman) packages base-devel python nodejs npm ripgrep fd fzf unzip curl git ;;
   zypper) packages gcc gcc-c++ make python3-devel nodejs npm ripgrep fd fzf unzip curl git ;;
  esac ;;
 tex)
  case "$PM" in
   apt) packages texlive-full latexmk biber ;;
   dnf) packages texlive-scheme-full latexmk biber ;;
   pacman) packages texlive-meta biber ;;
   zypper) packages texlive-scheme-full latexmk biber ;;
  esac ;;
 *) echo "[失败] 未知组件 $ACTION" >&2; exit 1 ;;
esac
if [ "$ACTION" = all ] || [ "$ACTION" = nvim ]; then
 if command -v nvim >/dev/null 2>&1; then
   nvim --version | head -n 1
   nvim --clean --headless '+lua if vim.fn.has("nvim-0.11.2")==0 then vim.cmd("cquit 1") end' +qa || {
    echo '[适配] 当前 Neovim 低于 0.11.2，使用经过 SHA256 校验的官方 v0.11.6 用户级安装。'
    ensure python3 python3
    python3 "$ROOT_DIR/scripts/install-nvim.py";
   }
 fi
fi
echo '[完成] DO=0 为预览，DO=1 为执行；没有自动切换默认登录 Shell。'
