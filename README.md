# nb-cli

[English](./README_en.md) | **中文**

NoneBot2 的命令行工具

## 功能

- 创建新的 Nonebot 项目
- 启动 Nonebot
- 部署 NoneBot 到 Docker
- 管理插件
  - 创建新的插件
  - 搜索/安装/更新/卸载在官方商店上发布的插件
- 管理适配器
  - 创建新的适配器
  - 搜索/安装/更新/卸载在官方商店上发布的适配器

## 使用

### 安装

```shell
pip install nb-cli
```

或者，带有可选的 `deploy` 依赖项

```shell
pip install nb-cli[deploy]
```

### 命令行使用

```shell
nb --help
```

- `nb init (create)` 创建新的 Nonebot 项目
- `nb run` 在当前目录启动 Nonebot
- `nb driver` 管理驱动器
  - `nb driver list` 查看驱动器列表
  - `nb driver search` 搜索驱动器
  - `nb driver install (add)` 安装驱动器
- `nb plugin` 管理插件
  - `nb plugin new (create)` 创建新的插件
  - `nb plugin list` 列出官方商店的所有插件
  - `nb plugin search` 在官方商店搜索插件
  - `nb plugin install (add)` 安装插件
  - `nb plugin update` 更新插件
  - `nb plugin uninstall (remove)` 卸载插件
- `nb adapter` 管理适配器
  - `nb adapter new (create)` 创建新的适配器
  - `nb adapter list` 列出官方商店的所有适配器
  - `nb adapter search` 在官方商店搜索适配器
  - `nb adapter install (add)` 安装适配器
  - `nb adapter update` 更新适配器
  - `nb adapter uninstall (remove)` 卸载适配器

#### 以下功能需要 [deploy] 依赖

- `nb build` 在当前目录构建 Docker 镜像
- `nb deploy (up)` 在当前目录构建、创建并运行 Docker 容器
- `nb exit (down)` 在当前目录停止并删除 Docker 容器

### 交互式使用

```shell
nb
```

### CookieCutter 使用

#### 安装 cookiecutter

```shell
pip install cookiecutter
```

#### 创建项目

```shell
cookiecutter https://github.com/nonebot/nb-cli.git --directory="nb_cli/project"
```

#### 创建插件

```shell
cookiecutter https://github.com/nonebot/nb-cli.git --directory="nb_cli/plugin"
```

#### 创建适配器

```shell
cookiecutter https://github.com/nonebot/nb-cli.git --directory="nb_cli/adapter"
```
