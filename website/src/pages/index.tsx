import React from "react";

import clsx from "clsx";

import CodeBlock from "@theme/CodeBlock";
import Layout from "@theme/Layout";

import { Hero, HeroFeature } from "../components/Hero";

import type { Feature } from "../components/Hero";

import styles from "./index.module.css";

import "@theme/Page" // TODO: remove this when nonepress 3.5.1 is ready

export default function Home() {
  const firstFeature: Feature = {
    title: "开箱即用",
    tagline: "out of box",
    description: "使用 NB-CLI 快速构建属于你的机器人",
  } as const;
  const secondFeatures = [
    {
      title: "插件系统",
      tagline: "plugin system",
      description: "支持插件和执行脚本",
    },
    {
      title: "跨语言支持",
      tagline: "i18n support",
      description: "支持多种语言，自动识别系统语言",
    },
  ] as const;

  return (
    <Layout>
      <Hero />
      <div className="max-w-7xl mx-auto py-16 px-4 text-center md:px-16">
        <HeroFeature {...firstFeature}>
          <CodeBlock
            title="Installation"
            className={clsx("inline-block", styles.homeCodeBlock)}
          >
            {[
              "$ pipx install nb-cli",
              "$ nb",
              "d8b   db  .d88b.  d8b   db d88888b d8888b.  .d88b.  d888888b",
              "888o  88 .8P  Y8. 888o  88 88'     88  `8D .8P  Y8. `~~88~~'",
              "88V8o 88 88    88 88V8o 88 88ooooo 88oooY' 88    88    88",
              "88 V8o88 88    88 88 V8o88 88~~~~~ 88~~~b. 88    88    88",
              "88  V888 `8b  d8' 88  V888 88.     88   8D `8b  d8'    88",
              "VP   V8P  `Y88P'  VP   V8P Y88888P Y8888P'  `Y88P'     YP",
              "[?] What do you want to do?",
              "❯ Create a NoneBot project.",
              "  Run the bot in current folder",
              "  Generate entry file of your bot",
              "  Manage bot plugins.",
              "  Manage bot adapters.",
              "  Manage bot driver.",
              "  ...",
            ].join("\n")}
          </CodeBlock>
        </HeroFeature>
      </div>
      <div className="max-w-7xl mx-auto py-16 px-4 md:grid md:grid-cols-2 md:gap-6 md:px-16">
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
                "[project.entry-points.nb]",
                'plugin_name = "cli_plugin.plugin:install"',
                "",
                "[project.entry-points.nb_scripts]",
                'foo = "awesome_bot.module:function"',
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
                "[?] 你想要进行什么操作?",
                "❯ 创建一个 NoneBot 项目.",
                "  管理 bot 插件.",
                "  管理 bot 适配器.",
                "  管理 bot 驱动器.",
              ].join("\n")}
            </CodeBlock>
          </HeroFeature>
        </div>
      </div>
    </Layout>
  );
}
