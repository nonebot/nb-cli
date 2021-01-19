# nb-cli

CLI for nonebot2

Features:

- Create A NoneBot Project
- Run NoneBot
- Deploy NoneBot to Docker
- Plugin Management
  - Create new plugins
  - Search for NoneBot Plugins Published on Official Store
  - Install NoneBot Plugin Published on Official Store

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

Creating a project

```shell
pip install cookiecutter
cookiecutter https://github.com/yanyongyu/nb-cli.git --directory="nb_cli/project"
```
