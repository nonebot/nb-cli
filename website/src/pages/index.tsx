import clsx from "clsx";
import React from "react";

import CodeBlock from "@theme/CodeBlock";
import Layout from "@theme/Layout";

import { Hero, HeroFeature } from "../components/Hero";
import type { Feature } from "../components/Hero";
import styles from "../css/index.module.css";

export default function Home() {
  const firstFeature: Feature = {
    title: "开箱即用",
    tagline: "out of box",
    description: "使用 NB-CLI 快速构建属于你的机器人",
  } as const;

  return (
    <Layout>
      <Hero />
      {
        <div className="max-w-7xl mx-auto py-16 px-4 text-center md:px-16">
          <HeroFeature {...firstFeature}>
            <CodeBlock
              title="Installation"
              className={clsx(
                "inline-block language-bash",
                styles.homeCodeBlock
              )}
            >
              {[
                "$ pip install nb-cli",
                "$ nb",
                "d8b   db  .d88b.  d8b   db d88888b d8888b.  .d88b.  d888888b",
                "888o  88 .8P  Y8. 888o  88 88'     88  `8D .8P  Y8. `~~88~~'",
                "88V8o 88 88    88 88V8o 88 88ooooo 88oooY' 88    88    88",
                "88 V8o88 88    88 88 V8o88 88~~~~~ 88~~~b. 88    88    88",
                "88  V888 `8b  d8' 88  V888 88.     88   8D `8b  d8'    88",
                "VP   V8P  `Y88P'  VP   V8P Y88888P Y8888P'  `Y88P'     YP",
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
        </div>
      }
    </Layout>
  );
}
