# nb-cli

**English** | [中文](./README.md)

CLI for nonebot2

## Features

- Create A NoneBot Project
- Run NoneBot
- Deploy NoneBot to Docker
- Plugin Management
  - Create new plugin
  - Search for NoneBot Plugins Published on Official Store
  - Install NoneBot Plugin Published on Official Store
  - Uninstall NoneBot Plugin Published on Official Store
  - Update NoneBot Plugin Published on Official Store
- Adapter Management
  - Create new adapter
  - Search for NoneBot Adapters Published on Official Store
  - Install NoneBot Adapters Published on Official Store
  - Uninstall NoneBot Adapters Published on Official Store
  - Update NoneBot Adapters Published on Official Store

## How to use

### Installation

```shell
pip install nb-cli
```

or, with optional `deploy` dependency

```shell
pip install nb-cli[deploy]
```

### Command-line usage

```shell
nb --help
```

### Interactive mode usage

```shell
nb
```

### CookieCutter usage

#### install cookiecutter

```shell
pip install cookiecutter
```

#### Creating a project

```shell
pip install cookiecutter
cookiecutter https://github.com/nonebot/nb-cli.git --directory="nb_cli/project"
```

#### Create new plugin

```shell
cookiecutter https://github.com/nonebot/nb-cli.git --directory="nb_cli/plugin"
```

#### Create new adapter

```shell
cookiecutter https://github.com/nonebot/nb-cli.git --directory="nb_cli/adapter"
```
