# 验证记录

验证机器：Ubuntu 26.04.1 / x86_64，2026-09-20。

已完成：

- `make test`：7 项通过。包含 Shell 语法、组件依赖、文本/链接 HOME 改写、真实 TeX 目录备份/复制/恢复、非法组件拒绝、Windows 217 个文件存在性、Fedora/Ubuntu/Debian/Arch/openSUSE 包管理器预览映射。
- 临时 HOME 的 Bash/Zsh 实际迁移和交互启动成功，退出码均为 0。Bash 在无 PTY 测试进程中仅提示 job control 不可用，无配置错误。
- 所有 Python 脚本通过语法解析。
- bootstrap 和 GRUB 的真实主机只读预览通过；没有在原机器运行系统安装或 GRUB 写入。
- Microsoft 目录 217 个字体文件；所有打包字体文件共 264 个，详见 FONT-INVENTORY.tsv。
- 五个 Rime LevelDB 用户词库按文件大小与纳秒修改时间核对，复制前后稳定；记录见 RIME-SNAPSHOT.json。未停止或重启用户现有输入法。
- SHA256 清单覆盖 payload、脚本、测试、Makefile、README、字体清单等；压缩包另有外部 SHA256。

未完成的外部环境验证：

- 没有 Fedora/Debian/Arch/openSUSE 虚拟机实际执行软件包安装；发行版测试是命令生成测试，不能代替仓库可用性检查。
- 未在新系统执行 GNOME 设置、登录、Fcitx5 重新部署或 GRUB 重启测试。
- 未在原机器运行会更新插件或下载语言服务器的 editor-runtime；目标机安装步骤会给出具体错误。
- 不保证不同 GNOME/Libadwaita/Flatpak 版本渲染完全相同；GTK4 CSS 独立选择。

本任务只在 Downloads/gnome 中生成迁移产物，以及临时目录中运行复制/恢复测试；没有替换当前物理机正在使用的配置。
