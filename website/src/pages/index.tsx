import clsx from "clsx";
import React from "react";

import CodeBlock from "@theme/CodeBlock";
import Layout from "@theme/Layout";

import { Hero, HeroFeature } from "../components/Hero";
import type { Feature } from "../components/Hero";
import styles from "../css/index.module.css";

export default function Home() {
  // const firstFeature: Feature = {
  //   title: "开箱即用",
  //   tagline: "out of box",
  //   description: "使用 NB-CLI 快速构建属于你的机器人",
  // } as const;
  // const secondFeatures = [
  //   {
  //     title: "插件系统",
  //     tagline: "plugin system",
  //     description: "插件化开发，模块化管理",
  //   },
  //   {
  //     title: "跨平台支持",
  //     tagline: "cross-platform support",
  //     description: "支持多种平台，以及多样的事件响应方式",
  //   },
  // ] as const;

  return (
    <Layout>
      <Hero />
      {/* <div className="max-w-7xl mx-auto py-16 px-4 text-center md:px-16">
        <HeroFeature {...firstFeature}>
          <CodeBlock
            title="Installation"
            className={clsx("inline-block language-bash", styles.homeCodeBlock)}
          >
            {[
              "$ pip install nb-cli",
              "$ nb",
              // "d8b   db  .d88b.  d8b   db d88888b d8888b.  .d88b.  d888888b",
              // "888o  88 .8P  Y8. 888o  88 88'     88  `8D .8P  Y8. `~~88~~'",
              // "88V8o 88 88    88 88V8o 88 88ooooo 88oooY' 88    88    88",
              // "88 V8o88 88    88 88 V8o88 88~~~~~ 88~~~b. 88    88    88",
              // "88  V888 `8b  d8' 88  V888 88.     88   8D `8b  d8'    88",
              // "VP   V8P  `Y88P'  VP   V8P Y88888P Y8888P'  `Y88P'     YP",
              "[?] What do you want to do?",
              "❯ Create a New Project",
              "  Run the Bot in Current Folder",
              "  Driver ->",
              "  Adapter ->",
              "  Plugin ->",
              "  ...",
            ].join("\n")}
          </CodeBlock>
        </HeroFeature>
      </div> */}
      {/* <div className="max-w-7xl mx-auto py-16 px-4 md:grid md:grid-cols-2 md:gap-6 md:px-16">
        <div className="pb-16 text-center md:pb-0">
          <HeroFeature {...secondFeatures[0]}>
            <CodeBlock
              title
              className={clsx(
                "inline-block language-python",
                styles.homeCodeBlock
              )}
            >
              {[
                "import nonebot",
                "# 加载一个插件",
                'nonebot.load_plugin("path.to.your.plugin")',
                "# 从文件夹加载插件",
                'nonebot.load_plugins("plugins")',
                "# 从配置文件加载多个插件",
                'nonebot.load_from_json("plugins.json")',
                'nonebot.load_from_toml("pyproject.toml")',
              ].join("\n")}
            </CodeBlock>
          </HeroFeature>
        </div>
        <div className="text-center">
          <HeroFeature {...secondFeatures[1]}>
            <CodeBlock
              title
              className={clsx(
                "inline-block language-python",
                styles.homeCodeBlock
              )}
            >
              {[
                "import nonebot",
                "# OneBot",
                "from nonebot.adapters.onebot.v11 import Adapter as OneBotAdapter",
                "# 钉钉",
                "from nonebot.adapters.ding import Adapter as DingAdapter",
                "driver = nonebot.get_driver()",
                "driver.register_adapter(OneBotAdapter)",
                "driver.register_adapter(DingAdapter)",
              ].join("\n")}
            </CodeBlock>
          </HeroFeature>
        </div>
      </div> */}
    </Layout>
  );
}
