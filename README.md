# GNOME 配置迁移包

## 从 GitHub 下载：先还原分卷

仓库：[faguomarry-ux/gnome](https://github.com/faguomarry-ux/gnome)。完整资源压缩包约 1.04 GiB，切成 **23 份、每份最多 48 MiB**，位于 `transfer/`。文档与脚本直接存放在 Git 中；`payload/` 在下载后恢复，不需要 Git LFS。

```sh
git clone https://github.com/faguomarry-ux/gnome.git
cd gnome
make unpack             # 或 python3 scripts/unpack.py
make verify
make help
# 然后按照下面“新机器使用顺序”安装与迁移
```

`make unpack` 按 parts.json 顺序合并，校验每份及整个压缩包的 SHA256，再只解压资源 `payload/`，最后校验整个迁移包。它不会把配置写入 HOME，不会安装程序。若 payload 已存在，只检查、不覆盖。

只下载 GitHub 单个分卷不能直接解压，必须取齐 23 份。下载仓库与 Git 对象、合并压缩包、解压资源会占用约 6–8 GiB 磁盘，请预留空间。分批上传期间仓库可能暂时未收齐分卷，须等待最终上传完成。

完全手动还原（在新 clone 且没有 payload 的目录）：

```sh
(cd transfer && sha256sum -c SHA256SUMS)
mkdir -p dist
cat transfer/gnome-config.tar.gz.part-* > dist/gnome-config.tar.gz
python3 - <<'PYVERIFY'
import hashlib,json
from pathlib import Path
meta=json.loads(Path('transfer/parts.json').read_text())
h=hashlib.sha256()
with Path('dist/gnome-config.tar.gz').open('rb') as f:
    for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
assert h.hexdigest()==meta['archive_sha256'], '完整压缩包校验失败'
print('完整压缩包 SHA256 正确')
PYVERIFY
tar -xzf dist/gnome-config.tar.gz ./payload
make verify
```

本仓库的分卷是一个固定快照；以后修改配置并 `make pack` 会生成新本地压缩包，但不会自动更新远程分卷。不要把 `payload/` 或整个 `dist/*.tar.gz` 强制加入 Git。


这是从 `/home/yyt` 的真实配置制作的快照，目标是 Fedora GNOME、Debian/Ubuntu GNOME，以及使用 pacman/zypper 的常规可变 Linux 系统。安装脚本支持这些包管理器；发行版实际安装与图形效果仍需在目标机器验证，不代表所有 GNOME 版本像素级相同。Atomic/Silverblue 会明确退出，不错误调用 dnf。

## 新机器使用顺序

以自己的普通用户登录 GNOME。不要 `sudo make`；脚本仅在安装包和复制系统资源时调用 sudo。

```sh
# 若尚无 make/python3：Fedora 使用 sudo dnf install make python3
# Debian/Ubuntu 使用 sudo apt-get install make python3
cd /解压位置/gnome
make help
make verify
make bootstrap                 # 默认预览
make bootstrap DO=1            # Bash、Zsh、Vim、Neovim、OMZ、Starship
make install-rime DO=1
make install-theme DO=1         # GNOME Tweaks
make editor-deps DO=1
make plan                      # 查看所有具体来源和目标
# 如果 fcitx5 正在运行，先在托盘菜单退出；新系统尚未启动则无需操作
make apply DO=1
make theme-settings DO=1        # 在真实 GNOME 桌面会话运行
make editor-runtime DO=1
make doctor
```

所有写入命令均默认预览；`make verify/test/pack/doctor` 是本地检查或产物生成，不受 DO 开关影响。`make apply` 不包含 GRUB、GTK4 CSS 和旧机器二进制运行环境。安装、文件迁移、GNOME 设置分别调用，便于分项维护。安装需要网络及 sudo；文件迁移本身离线可用。现有 Neovim 低于 0.11.2 时，x86_64/aarch64 会使用已固定 SHA256 的官方 v0.11.6 包安装到 `~/.local/opt/nvim-v0.11.6`，命令链接为 `~/.local/bin/nvim`；不添加第三方 PPA。其他架构报告需手工升级。

注销并重新登录以加载输入法环境变量及字体。Fcitx5 的配置、启动项和雾凇词库已恢复；首次启动执行“重新部署”，重新生成目标 librime 对应的 build。Debian/Ubuntu 可再执行 `im-config -n fcitx5`。Fedora 使用打包的 environment.d 与 autostart；GNOME Wayland 中不同应用的输入法支持仍受其 GTK/Qt/沙盒后端影响。

如果希望默认登录 Zsh，自行执行 `chsh -s "$(command -v zsh)"` 后注销。脚本不修改登录 Shell。

## 分项操作与路径

```sh
make apply-bash DO=1
make apply-zsh DO=1
make apply-oh-my-zsh DO=1
make apply-starship DO=1
make apply-vim DO=1
make apply-nvim DO=1
make apply-tex DO=1
make apply-rime DO=1
make apply-theme DO=1
make apply-fonts DO=1
make plan COMPONENT=rime
make install-zsh DO=1           # install-bash/vim/nvim/oh-my-zsh/starship 同理
```

| 组件 | 目标路径 | 说明 |
|---|---|---|
| common | `~/.config/shell/common`、同级 README | Bash/Zsh 公共环境、函数、别名 |
| bash | `~/.bashrc`、`~/.profile`、`~/.bash_logout`、`~/.config/shell/bash`、`~/.local/share/blesh` | 自动带 common 和 Starship 配置 |
| zsh | `~/.zshrc`、`~/.zprofile`、`~/.p10k.zsh`、`~/.config/shell/zsh` | 自动带 common、Oh My Zsh；当前提示符仍为 Powerlevel10k |
| oh-my-zsh | `~/.oh-my-zsh` | 包含实际 custom 插件与主题源码 |
| starship | `~/.config/starship.toml` | Bash 当前提示符配置；程序由 bootstrap 安装 |
| vim | `~/.vimrc`、`~/.vim/{config,autoload,plugged,coc-settings.json}`、`~/Templates`、`~/.config/coc` | 含模板和 CoC 扩展 |
| nvim | `~/.config/nvim`、`~/.local/share/nvim/{lazy,language.txt}` | 保留 lazy-lock.json 和插件源码 |
| tex | `~/.config/shell/tex`、`~/.latexrc` | 两个编译脚本；自动带 common |
| rime | `~/.local/share/fcitx5/rime`、`~/.config/fcitx5`、环境变量、自动启动、`~/.xinputrc` | 含自定义词典、Lua、用户词库；迁移时移除可重建 build 和 LOCK |
| theme | `~/.themes`、`~/.local/share/icons`、`~/.config/gtk-3.0`、实际壁纸路径、`/usr/share/icons/whiteglass` | 系统 cursor 原路径需要 sudo |
| fonts | `~/.local/share/fonts`、`/usr/share/fonts/truetype/ubuntu` | 保留原始字体和原位置，完成后刷新缓存 |
| gtk4 | `~/.config/gtk-4.0` | 单独 `make gtk4-apply DO=1` |
| grub | 原始 `/etc/default/grub`、grub.d、主题完整存档 | 实际迁移用下文专用命令 |
| runtime | 原始 Mason、Treesitter site、editor-python 快照 | 仅存档，避免跨 libc/架构搬运二进制 |

完整清单见 `manifest.json`，记录每个组件、源路径、包内路径、目标路径与未发现的可选文件；`checksums.json` 包含逐文件/符号链接的 SHA256。目录迁移会整体替换表中对应目录，目标原目录先完整备份，不会悄悄合并不兼容的旧文件。例如迁移 Vim 会替换 Templates；请先检查 plan。

同名用户 yyt 的路径与原机一致；不同用户名保留相对 HOME 的结构，并替换 UTF-8 文本和绝对链接里的 `/home/yyt`。不会重写二进制文件。若目标主动配置了 XDG_CONFIG_HOME/NVIM_APPNAME/ZDOTDIR 到其他位置，本包仍写入表中原结构，须先统一这些变量。

## GNOME 外观

实际读取值：WhiteSur-Light（GTK）、WhiteSur-dark（图标）、whiteglass（光标），颜色偏好深色，文字缩放 1.25；壁纸以快照时机器的 GSettings 为准，和提供截图的壁纸不同。保存的是主题/字体/壁纸相关键，没有把整台机器 dconf 数据库覆盖到另一台机器。

`make theme-settings DO=1` 检查目标 schema/key，旧版本缺少 accent-color 等键会明确报告跳过，写入失败则非零退出。GTK4 CSS 对版本敏感，因此单独应用；Libadwaita/Flatpak 与旧 GTK 应用可能呈现不同效果。没有迁移或强制启用无关 GNOME 扩展，没有关闭扩展版本检查。

## GRUB 单独操作

```sh
make grub-plan
make grub-apply DO=1
```

完整原文件保存在 `payload/grub/system/`。应用只写 WhiteSur 主题、分辨率与菜单时间，保留目标机器的 GRUB_DEFAULT、内核命令行、UUID、BLS 等。

原机隐藏菜单且等待 0 秒；迁移默认显示菜单 5 秒，便于新机器选择系统。需要原样菜单行为时执行 `python3 scripts/grub.py --original-timeout --execute`。此功能迁移的是外观，不会自动发现或新建其他操作系统的启动项，也不会安装引导器。

Fedora 自动使用 `/boot/grub2/themes/whitesur` 与 `grub2-mkconfig -o /boot/grub2/grub.cfg`；Debian/Ubuntu 使用 `/boot/grub/themes/whitesur` 与 `update-grub`。不会将 Fedora 的 EFI 转发文件当成生成目标。

原配置、已有主题和生成前 grub.cfg 备份在 `/var/backups/gnome-migrate/时间戳/`。生成失败会恢复原配置与 grub.cfg；主题目录备份仍保留。需要手工恢复：将备份的 `grub` 复制回 `/etc/default/grub`，按终端显示的目标主题路径恢复 `whitesur`，再执行对应系统的配置生成命令。

## 恢复与验证

每次文件迁移在 `~/.local/state/gnome-migrate/时间戳/` 保存原内容及 restore.json，记录新建路径；即使中途失败，已经写入的项目也可以恢复。

```sh
make restore BACKUP=/完整路径/restore.json             # 先预览
make restore BACKUP=/完整路径/restore.json DO=1
make settings-restore BACKUP=/完整路径/settings-日期.json DO=1
make test
make pack
```

恢复会替换对应路径，包括删除当时新建的路径。请在开始使用配置前确认结果，恢复前自行保留后来新加的内容。GNOME 设置有独立备份；恢复后字体可执行 `fc-cache -f`，输入法应退出后再恢复。

压缩包生成在 `dist/gnome-config.tar.gz`，附 SHA256。新机器先 `sha256sum -c gnome-config.tar.gz.sha256`，再新建目录解压，运行 `make verify`。压缩包包含个人词库、字体和配置，适合个人备份迁移；不是去隐私或可公开再分发的发行包。

## 依赖边界

- **已打包配置和相关资源**：完整 Shell 模块、两套编辑器插件源码、雾凇词典/自定义内容/用户词库、TeX 脚本、主题、壁纸、字体及 GRUB 存档。
- **不搬整套开发环境**：Cargo/Rustup、CUDA、NVM/Pyenv/Mamba、OpenFOAM、TeX Live 本体等由目标机器安装；原有 shell 配置大多按命令/目录是否存在加载。别名仍可能依赖额外命令。`make install-tex DO=1` 可安装发行版完整 TeX（较大，默认不执行）。
- **编辑器二进制**：Mason/venv/site 已完整存档但不默认复制。`make editor-deps DO=1`、`make editor-runtime DO=1` 后，会等待并重建源机器记录的 14 个 Mason 工具，安装失败返回非零；完成后执行 `:checkhealth`。Vim CoC 复用 `~/.local/share/nvim/mason/bin/` 下的 clangd/rust-analyzer/texlab，须在 Mason 安装这些工具。运行时下载需要网络，源端二进制快照不等于目标端已验证可用。
- 不迁移 Shell 历史、Vim 撤销历史、SSH/GPG 密钥、浏览器状态或整套系统设置；所列配置中的个人绝对路径和署名会保留（仅 HOME 适配）。

## 参考

- Fedora GRUB 官方说明：https://fedoraproject.org/wiki/GRUB_2
- Fedora fcitx5-rime 包：https://packages.fedoraproject.org/pkgs/fcitx5-rime/fcitx5-rime/
- Starship 官方安装：https://starship.rs/

## Windows 字体：完整迁移与单独迁移

源机器的 `~/.local/share/fonts/Microsoft/` **217 个字体文件已全部收录**（目录内也有其他来源的字体，按原目录原样保留）。包含微软雅黑、等线、Arial、Times New Roman、Calibri、Cambria/Cambria Math、Consolas、Segoe 等。实际文件清单见 `FONT-INVENTORY.tsv`，逐文件完整性由 checksums.json 校验。

```sh
# 只迁移 Microsoft 目录，不替换其他用户字体目录
make plan COMPONENT=windows-fonts
make apply-windows-fonts DO=1
# 与上述命令完全等效的脚本调用
python3 scripts/migrate.py apply windows-fonts --execute

# 全部字体（Microsoft、MapleMono、0xProto、原系统 Ubuntu 字体）
make apply-fonts DO=1
python3 scripts/migrate.py apply fonts --execute

# 手动更新缓存和检查是否真正匹配了预期字体
fc-cache -f
fc-match 'Microsoft YaHei' -f '%{family}: %{file}\n'
fc-match 'Times New Roman' -f '%{family}: %{file}\n'
fc-match 'Cambria Math' -f '%{family}: %{file}\n'
fc-match 'Consolas' -f '%{family}: %{file}\n'
fc-list :lang=zh family file
```

`fc-match` 即使缺少字体也可能返回替代字体，所以请检查 family 和文件路径是否落在迁移的 Microsoft 目录。安装完成后重启 Word/WPS/LibreOffice/TeX 编辑器等程序。XeLaTeX/LuaLaTeX 可以使用这些系统字体；pdfLaTeX 的字体机制不同，复制 TTF 不会让它自动支持 fontspec。

完全手动仅复制 Windows 字体（本段自行备份目标目录，不依赖迁移脚本）：

```sh
# 在包根目录运行；不需要 sudo
FONT_BACKUP="$HOME/.local/state/gnome-font-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$FONT_BACKUP" "$HOME/.local/share/fonts"
if [ -e "$HOME/.local/share/fonts/Microsoft" ]; then
    mv "$HOME/.local/share/fonts/Microsoft" "$FONT_BACKUP/Microsoft"
fi
cp -a payload/fonts/home/.local/share/fonts/Microsoft "$HOME/.local/share/fonts/Microsoft"
fc-cache -f
printf '目标：%s\n旧字体备份：%s\n' "$HOME/.local/share/fonts/Microsoft" "$FONT_BACKUP"
```

## 不用 Make：每个脚本的等效命令

以下命令均在迁移包根目录执行。`sh` 安装脚本用环境变量 `DO=1`，Python 迁移脚本用 `--execute`；省略它们就只预览。下面每一行都是独立操作，不需要同时执行 Make 与对应脚本，否则会重复操作。

| 任务 | Make 写法 | 不用 Make 的完全等效写法 |
|---|---|---|
| 基础程序检测安装 | `make bootstrap DO=1` | `DO=1 sh scripts/bootstrap.sh all` |
| 安装 Bash | `make install-bash DO=1` | `DO=1 sh scripts/bootstrap.sh bash` |
| 安装 Zsh | `make install-zsh DO=1` | `DO=1 sh scripts/bootstrap.sh zsh` |
| 安装 Vim | `make install-vim DO=1` | `DO=1 sh scripts/bootstrap.sh vim` |
| 安装 Neovim | `make install-nvim DO=1` | `DO=1 sh scripts/bootstrap.sh nvim` |
| 安装 OMZ | `make install-oh-my-zsh DO=1` | `DO=1 sh scripts/bootstrap.sh oh-my-zsh` |
| 安装 Starship | `make install-starship DO=1` | `DO=1 sh scripts/bootstrap.sh starship` |
| 安装输入法 | `make install-rime DO=1` | `DO=1 sh scripts/bootstrap.sh rime` |
| 安装 Tweaks | `make install-theme DO=1` | `DO=1 sh scripts/bootstrap.sh theme` |
| 安装完整 TeX | `make install-tex DO=1` | `DO=1 sh scripts/bootstrap.sh tex` |
| 安装编辑器依赖 | `make editor-deps DO=1` | `DO=1 sh scripts/bootstrap.sh editor-deps` |
| 重建编辑器运行环境 | `make editor-runtime DO=1` | `DO=1 sh scripts/editor-runtime.sh` |
| 全部文件迁移 | `make apply DO=1` | `python3 scripts/migrate.py apply all --execute` |
| 迁移公共模块 | `make apply-common DO=1` | `python3 scripts/migrate.py apply common --execute` |
| 迁移 Bash | `make apply-bash DO=1` | `python3 scripts/migrate.py apply bash --execute` |
| 迁移 Zsh | `make apply-zsh DO=1` | `python3 scripts/migrate.py apply zsh --execute` |
| 迁移 OMZ | `make apply-oh-my-zsh DO=1` | `python3 scripts/migrate.py apply oh-my-zsh --execute` |
| 迁移 Starship | `make apply-starship DO=1` | `python3 scripts/migrate.py apply starship --execute` |
| 迁移 Vim | `make apply-vim DO=1` | `python3 scripts/migrate.py apply vim --execute` |
| 迁移 Neovim | `make apply-nvim DO=1` | `python3 scripts/migrate.py apply nvim --execute` |
| 迁移 TeX 脚本 | `make apply-tex DO=1` | `python3 scripts/migrate.py apply tex --execute` |
| 迁移雾凇配置 | `make apply-rime DO=1` | `python3 scripts/migrate.py apply rime --execute` |
| 迁移主题资源 | `make apply-theme DO=1` | `python3 scripts/migrate.py apply theme --execute` |
| 应用桌面外观 | `make theme-settings DO=1` | `python3 scripts/migrate.py settings --execute` |
| 应用 GTK4 覆盖 | `make gtk4-apply DO=1` | `python3 scripts/migrate.py apply gtk4 --execute` |
| GRUB 外观 | `make grub-apply DO=1` | `python3 scripts/grub.py --execute` |
| 校验包 | `make verify` | `python3 scripts/migrate.py verify` |
| 环境检查 | `make doctor` | `python3 scripts/doctor.py` |
| 测试 | `make test` | `python3 -B tests/test_migration.py` |
| 恢复文件 | `make restore BACKUP=/path/restore.json DO=1` | `python3 scripts/migrate.py restore --backup /path/restore.json --execute` |
| 恢复桌面设置 | `make settings-restore BACKUP=/path/settings.json DO=1` | `python3 scripts/migrate.py settings-restore --backup /path/settings.json --execute` |

无需 Make 的打包：

```sh
python3 scripts/migrate.py verify
mkdir -p dist
tar --exclude='./dist' --exclude='./transfer' --exclude='./.git' --exclude='__pycache__' -I 'gzip -1' -cf dist/gnome-config.tar.gz.tmp .
mv dist/gnome-config.tar.gz.tmp dist/gnome-config.tar.gz
(cd dist && sha256sum gnome-config.tar.gz > gnome-config.tar.gz.sha256)
```

## 完全手动安装基础工具（不运行本包脚本）

按目标发行版选择一组，不要全部执行。已经安装的包会由包管理器识别。

```sh
# Fedora Workstation
sudo dnf install bash zsh vim neovim git curl make python3 gnome-tweaks
sudo dnf install fcitx5 fcitx5-rime librime-lua fcitx5-chinese-addons fcitx5-gtk fcitx5-qt fcitx5-configtool
sudo dnf install gcc gcc-c++ python3-devel nodejs npm ripgrep fd-find fzf unzip

# Debian / Ubuntu
sudo apt-get update
sudo apt-get install bash zsh vim neovim git curl make python3 gnome-tweaks
sudo apt-get install fcitx5 fcitx5-rime librime-plugin-lua fcitx5-chinese-addons fcitx5-frontend-gtk3 fcitx5-frontend-gtk4 fcitx5-frontend-qt5 fcitx5-config-qt im-config
sudo apt-get install build-essential python3-venv python3-dev nodejs npm ripgrep fd-find fzf unzip

# Arch 系
sudo pacman -S --needed bash zsh vim neovim git curl make python gnome-tweaks
sudo pacman -S --needed fcitx5 fcitx5-rime fcitx5-chinese-addons fcitx5-gtk fcitx5-qt fcitx5-configtool

# openSUSE
sudo zypper install bash zsh vim neovim git curl make python3 gnome-tweaks
sudo zypper install fcitx5 fcitx5-rime fcitx5-gtk fcitx5-qt fcitx5-configtool
```

检查命令位置与版本：

```sh
command -v bash zsh vim nvim git curl make python3
bash --version
zsh --version
vim --version
nvim --version
```

本配置使用的 LazyVim 要求 Neovim >= 0.11.2。旧 Debian/Ubuntu 仓库版本可能不足；`bootstrap.sh` 会自动安装固定版本官方包，手动操作则应从 Neovim 官方 release 获取对应架构版本并核验 SHA256。不要因 `nvim` 命令存在就认定版本满足要求。

Starship 手动安装：

```sh
mkdir -p "$HOME/.local/bin"
curl --fail --location --proto '=https' --tlsv1.2 https://starship.rs/install.sh -o /tmp/starship-install.sh
sh /tmp/starship-install.sh --yes --bin-dir "$HOME/.local/bin"
"$HOME/.local/bin/starship" --version
```

Oh My Zsh 推荐直接恢复包内 `.oh-my-zsh`，包含当前 Powerlevel10k 和自定义插件；只 `git clone https://github.com/ohmyzsh/ohmyzsh.git ~/.oh-my-zsh` 不会带回个人插件。

## 完全手动复制配置：逐组件命令

以下用于了解每个路径和复现复制过程。**同用户名 `/home/yyt` 时原内容可直接使用；不同用户名请优先使用迁移脚本，它会额外改写文本绝对路径与绝对符号链接。** 手动命令不会自动执行这种适配，也不会生成脚本格式的恢复索引。

先在包根目录启动 Bash，将下面辅助函数粘贴到当前终端。它会把即将覆盖的目标移到备份目录，再复制整个原始文件/目录；该备份不会删除。

```bash
MANUAL_BACKUP="$HOME/.local/state/gnome-manual-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$MANUAL_BACKUP"
copy_home() {
    local component="$1" rel="$2" src="payload/$1/home/$2" dst="$HOME/$2"
    [ -e "$src" ] || [ -L "$src" ] || { printf '缺少源文件：%s\n' "$src"; return 1; }
    mkdir -p "$(dirname "$dst")" "$MANUAL_BACKUP/$(dirname "$rel")"
    if [ -e "$dst" ] || [ -L "$dst" ]; then
        [ ! -e "$MANUAL_BACKUP/$rel" ] && [ ! -L "$MANUAL_BACKUP/$rel" ] || { echo '该路径本轮已备份，请新建备份目录'; return 1; }
        mv "$dst" "$MANUAL_BACKUP/$rel" || return
    fi
    cp -a "$src" "$dst" || return
    printf '已复制：%s -> %s\n备份目录：%s\n' "$src" "$dst" "$MANUAL_BACKUP"
}
```

### Bash、Zsh 与共享模块

公共模块先复制一次；Bash 和 Zsh 都引用它。

```bash
copy_home common .config/shell/common
copy_home common .config/shell/README.md

# Bash（包含 ble.sh 的高亮与补全，提示符是 Starship）
copy_home bash .bashrc
copy_home bash .profile
copy_home bash .bash_logout
copy_home bash .config/shell/bash
copy_home bash .local/share/blesh
copy_home starship .config/starship.toml
bash -n "$HOME/.bashrc"
# 新开终端，或 exec bash

# Zsh（包含 Powerlevel10k，不替换成 Starship）
copy_home oh-my-zsh .oh-my-zsh
copy_home zsh .zshrc
copy_home zsh .zprofile
copy_home zsh .p10k.zsh
copy_home zsh .config/shell/zsh
zsh -n "$HOME/.zshrc"
# 新开 zsh，或 exec zsh
```

重新加载只适用于已在运行的对应 Shell：Bash 用 `source ~/.bashrc`，Zsh 用 `source ~/.zshrc`；跨 Shell 不要互相 source 配置。

### Vim

```bash
copy_home vim .vimrc
copy_home vim .vim/config
copy_home vim .vim/autoload
copy_home vim .vim/plugged
copy_home vim .vim/coc-settings.json
copy_home vim Templates
copy_home vim .config/coc
copy_home vim .config/EDITORS.md
copy_home vim .config/vim-templates.md
vim
```

Vim 内运行 `:PlugStatus` 查看插件，`:CocInfo` 检查补全，`:messages` 查启动错误。CoC 需要 node；clangd、rust-analyzer、texlab 的路径复用 Neovim 的 Mason，请完成下面的运行环境重建。手动 `:PlugInstall` 可补缺失插件；`:PlugUpdate` 会升级插件，和恢复快照不是同一件事。

### Neovim 与语言工具

```bash
copy_home nvim .config/nvim
copy_home nvim .local/share/nvim/lazy
copy_home nvim .local/share/nvim/language.txt
python3 -m venv "$HOME/.local/share/editor-python"
"$HOME/.local/share/editor-python/bin/python" -m pip install pynvim debugpy virtualenv
nvim --headless '+Lazy! restore' '+Lazy! build' +qa
nvim
```

在 Neovim 内执行以下命令，等待安装完成，再 `:checkhealth`：

```vim
:MasonInstall basedpyright clangd codelldb debugpy latexindent lua-language-server prettier ruff rust-analyzer shfmt stylua taplo texlab tree-sitter-cli
:Mason
:checkhealth
```

`make editor-runtime DO=1` 会自动等待上述 14 个工具安装完成并报告失败。编译器、Node/npm、Python venv、网络缺一都可能导致个别 Mason 包安装失败，先看 `:MasonLog`。Treesitter 解析器及插件自己的原生构建由目标机器重建，不直接使用旧系统的 site/parser 二进制。

### TeX 编译脚本

```bash
copy_home tex .config/shell/tex
copy_home tex .latexrc
# 若未做 Shell 迁移，还需要复制 common；见上文，勿重复覆盖同轮备份。
# 查看两个脚本自带说明
bash "$HOME/.config/shell/tex/latexcompile-simple.sh" --help
bash "$HOME/.config/shell/tex/latexcompile-standalone.sh" --help
command -v xelatex latexmk biber
```

已恢复的 Shell 别名 `texmk` / `texmkone` 指向这两个文件。现有公共 TeX 环境优先检测 `/usr/local/texlive/2026/bin/x86_64-linux`，路径不存在则不注入。改用发行版 TeX 时不必建立假的旧路径；需要自定义原版 TeX Live 安装位置时修改 `~/.config/shell/common/15-texlive.sh`。

### Fcitx5 + Rime 雾凇

在 Fcitx5 菜单退出输入法后执行，避免覆盖正在打开的用户词库。

```bash
copy_home rime .local/share/fcitx5/rime
copy_home rime .config/fcitx5
copy_home rime .config/environment.d/fcitx.conf
copy_home rime .config/autostart/org.fcitx.Fcitx5.desktop
copy_home rime .xinputrc
# build 是目标 librime 可重建的缓存，先移到手动备份而不是沿用旧 ABI
if [ -d "$HOME/.local/share/fcitx5/rime/build" ]; then
    mv "$HOME/.local/share/fcitx5/rime/build" "$MANUAL_BACKUP/rime-build"
fi
# Debian/Ubuntu 专用选择命令；Fedora 不运行此命令
im-config -n fcitx5
```

注销后登录，Fcitx5 菜单选择重新部署。若输入法未启动，运行 `fcitx5 -d`，用 `fcitx5-configtool` 检查 Rime 是否在当前组；`fcitx5-diagnose` 输出前端/环境诊断。不要用 ibus-rime 的配置目录替换本包路径：当前包针对的是 Fcitx5 Rime。

### 主题、壁纸、GTK4 和字体

```bash
copy_home theme .themes
copy_home theme .local/share/icons
copy_home theme .config/gtk-3.0
# GTK4 可选，先确认目标版本；迁移脚本会适配不同 HOME 的链接
copy_home gtk4 .config/gtk-4.0
# 全部用户字体；若之前已单独复制 Microsoft，选择此项会整体替换 fonts 目录
copy_home fonts .local/share/fonts
```

系统级 whiteglass 光标和 Ubuntu 字体的手动操作（保留原系统路径）：

```sh
SYSTEM_BACKUP="/var/backups/gnome-manual-$(date +%Y%m%d-%H%M%S)"
sudo mkdir -p "$SYSTEM_BACKUP" /usr/share/icons /usr/share/fonts/truetype
if [ -e /usr/share/icons/whiteglass ]; then
    sudo mv /usr/share/icons/whiteglass "$SYSTEM_BACKUP/whiteglass"
fi
sudo cp -a payload/theme/system/usr/share/icons/whiteglass /usr/share/icons/whiteglass
if [ -e /usr/share/fonts/truetype/ubuntu ]; then
    sudo mv /usr/share/fonts/truetype/ubuntu "$SYSTEM_BACKUP/ubuntu-fonts"
fi
sudo cp -a payload/fonts/system/usr/share/fonts/truetype/ubuntu /usr/share/fonts/truetype/ubuntu
sudo chown -R root:root /usr/share/icons/whiteglass /usr/share/fonts/truetype/ubuntu
fc-cache -f
```

GNOME 常用设置的直接命令：

```sh
# 保存本次操作前的值，恢复时用相同 schema/key 和保存的值
for key in gtk-theme icon-theme cursor-theme color-scheme font-name monospace-font-name text-scaling-factor; do
    printf '%s = ' "$key"
    gsettings get org.gnome.desktop.interface "$key"
done

gsettings set org.gnome.desktop.interface gtk-theme 'WhiteSur-Light'
gsettings set org.gnome.desktop.interface icon-theme 'WhiteSur-dark'
gsettings set org.gnome.desktop.interface cursor-theme 'whiteglass'
gsettings set org.gnome.desktop.interface color-scheme 'prefer-dark'
gsettings set org.gnome.desktop.interface font-name 'Ubuntu Sans 11'
gsettings set org.gnome.desktop.interface monospace-font-name 'Ubuntu Sans Mono 11'
gsettings set org.gnome.desktop.interface text-scaling-factor 1.25
# 当前快照的所有键和值（包括具体壁纸 URI）
cat gnome-settings.json
```

壁纸文件位置见 manifest.json 中 component=theme 的 source/dest 条目：复制到相同的 HOME 相对路径，再设置 `org.gnome.desktop.background picture-uri` 和 `picture-uri-dark`。例如自己指定另一张壁纸：

```sh
# 将例子替换为真实图片路径；Python 会正确编码空格和中文
WALLPAPER_URI=$(python3 -c 'from pathlib import Path; print((Path.home()/"Pictures/my-wallpaper.png").as_uri())')
gsettings set org.gnome.desktop.background picture-uri "'$WALLPAPER_URI'"
gsettings set org.gnome.desktop.background picture-uri-dark "'$WALLPAPER_URI'"
gsettings set org.gnome.desktop.background picture-options 'zoom'
```

要完整恢复快照所有键、自动跳过目标不支持的键、记录原值备份，应使用 `python3 scripts/migrate.py settings --execute`。上面的常用命令只展示操作原理，不宣称覆盖所有键。

### GRUB 的手动等效操作

先备份，再编辑 **目标机器原有** `/etc/default/grub`，不要把包内整份 Ubuntu grub 文件覆盖到 Fedora：

```sh
sudo cp -a /etc/default/grub "/etc/default/grub.before-gnome-$(date +%Y%m%d-%H%M%S)"
sudoedit /etc/default/grub
```

修改/添加（原有同名键只保留一处）：

```ini
GRUB_GFXMODE=2560x1440,auto
GRUB_TIMEOUT_STYLE=menu
GRUB_TIMEOUT=5
# Fedora 使用这一行：
GRUB_THEME="/boot/grub2/themes/whitesur/theme.txt"
# Debian/Ubuntu 则用：GRUB_THEME="/boot/grub/themes/whitesur/theme.txt"
```

主题复制和配置生成二选一；已有 whitesur 目录应先 `sudo mv` 到自己记录的备份路径：

```sh
# Fedora
sudo mkdir -p /boot/grub2/themes
sudo cp -a payload/grub/system/boot/grub/themes/whitesur /boot/grub2/themes/
sudo chown -R root:root /boot/grub2/themes/whitesur
sudo grub2-mkconfig -o /boot/grub2/grub.cfg

# Debian / Ubuntu
sudo mkdir -p /boot/grub/themes
sudo cp -a payload/grub/system/boot/grub/themes/whitesur /boot/grub/themes/
sudo chown -R root:root /boot/grub/themes/whitesur
sudo update-grub
```

脚本版额外提供自动系统识别、生成前备份和失败回滚，手动操作应自己保留输出并确认生成成功。

雾凇及自定义 Lua 组件需要 librime 的 Lua 支持，不能只安装 fcitx5-rime：Fedora 安装 `librime-lua`，Debian/Ubuntu 安装 `librime-plugin-lua`，安装脚本已包含。参考：[Fedora librime-lua](https://packages.fedoraproject.org/pkgs/librime/librime-lua/) 与 [Debian librime-plugin-lua](https://packages.debian.org/trixie/libs/librime-plugin-lua)。
