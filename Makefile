SHELL := /bin/sh
.DEFAULT_GOAL := help
.NOTPARALLEL:
DO ?= 0
COMPONENT ?= all
BACKUP ?=
TARGET_HOME ?=
export DO
EXECUTE = $(if $(filter 1,$(DO)),--execute,)
TARGET = $(if $(TARGET_HOME),--target-home "$(TARGET_HOME)",)
COMPONENTS := common bash zsh oh-my-zsh starship vim nvim tex rime theme fonts windows-fonts gtk4
INSTALL_COMPONENTS := bash zsh vim nvim oh-my-zsh starship rime theme tex
.PHONY: unpack help bootstrap plan apply verify doctor pack test theme-settings gtk4-apply grub-plan grub-apply restore settings-restore editor-deps editor-runtime $(addprefix apply-,$(COMPONENTS)) $(addprefix install-,$(INSTALL_COMPONENTS))
unpack:
	@python3 scripts/unpack.py
help:
	@printf '%s\n' 'GNOME 配置迁移包（默认预览，DO=1 才写入）' 'make bootstrap DO=1                基础工具检测/安装' 'make install-rime DO=1              安装 Fcitx5/Rime' 'make plan [COMPONENT=zsh]           显示来源与目标' 'make apply DO=1                    迁移用户配置、主题与字体（不含 GRUB/GTK4/二进制快照）' 'make apply-zsh DO=1                单项迁移，自动带公共模块与 Oh My Zsh' 'make theme-settings DO=1           应用桌面主题、字体、壁纸设置' 'make gtk4-apply DO=1                可选 GTK4 CSS 覆盖' 'make grub-plan                     独立预览 GRUB 外观方案' 'make grub-apply DO=1                应用 GRUB 外观并重建' 'make editor-deps DO=1               编辑器编译/LSP 依赖' 'make editor-runtime DO=1            重建编辑器 Python/插件运行环境' 'make verify / doctor / test / pack  校验、诊断、测试、压缩' 'make restore BACKUP=/.../restore.json DO=1  按索引恢复文件' 'make settings-restore BACKUP=/.../settings-日期.json DO=1' '可用组件：$(COMPONENTS)'
bootstrap:
	@sh scripts/bootstrap.sh all
$(addprefix install-,$(INSTALL_COMPONENTS)):
	@sh scripts/bootstrap.sh $(@:install-%=%)
plan:
	@python3 scripts/migrate.py apply "$(COMPONENT)" $(TARGET)
apply:
	@python3 scripts/migrate.py apply "$(COMPONENT)" $(EXECUTE) $(TARGET)
$(addprefix apply-,$(COMPONENTS)):
	@python3 scripts/migrate.py apply "$(@:apply-%=%)" $(EXECUTE) $(TARGET)
theme-settings:
	@python3 scripts/migrate.py settings $(EXECUTE)
gtk4-apply: apply-gtk4
grub-plan:
	@python3 scripts/grub.py
grub-apply:
	@python3 scripts/grub.py $(EXECUTE)
verify:
	@python3 scripts/migrate.py verify
doctor:
	@python3 scripts/doctor.py
restore:
	@test -n "$(BACKUP)" || { echo '需要 BACKUP=/完整路径/restore.json'; exit 1; }
	@python3 scripts/migrate.py restore --backup "$(BACKUP)" $(EXECUTE)
settings-restore:
	@test -n "$(BACKUP)" || { echo '需要 BACKUP=/完整路径/settings-日期.json'; exit 1; }
	@python3 scripts/migrate.py settings-restore --backup "$(BACKUP)" $(EXECUTE)
editor-deps:
	@sh scripts/bootstrap.sh editor-deps
editor-runtime:
	@sh scripts/editor-runtime.sh
test:
	@python3 -B tests/test_migration.py
pack: verify
	@mkdir -p dist
	@tar --exclude='./dist' --exclude='./transfer' --exclude='./.git' --exclude='__pycache__' -I 'gzip -1' -cf dist/gnome-config.tar.gz.tmp .
	@mv dist/gnome-config.tar.gz.tmp dist/gnome-config.tar.gz
	@cd dist && sha256sum gnome-config.tar.gz > gnome-config.tar.gz.sha256
	@printf '已生成：%s/dist/gnome-config.tar.gz\n' "$(CURDIR)"
