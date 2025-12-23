import React from "react";

import CodeBlock from "@theme/CodeBlock";

export type Feature = {
  title: string;
  tagline?: string;
  description?: string;
  annotaion?: string;
  children?: React.ReactNode;
};

export function HomeFeature({
  title,
  tagline,
  description,
  annotaion,
  children,
}: Feature): React.ReactNode {
  return (
    <div className="flex flex-col items-center justify-center p-4">
      <p className="text-sm text-base-content/70 font-medium tracking-wide uppercase">
        {tagline}
      </p>
      <h1 className="mt-3 font-mono font-light text-4xl tracking-tight sm:text-5xl md:text-5xl text-primary">
        {title}
      </h1>
      <p className="mt-10 mb-6">{description}</p>
      {children}
      <p className="text-sm italic text-base-content/70">{annotaion}</p>
    </div>
  );
}

function HomeFeatureSingleColumn(props: Feature): React.ReactNode {
  return (
    <div className="grid grid-cols-1 px-4 py-8 md:px-16 mx-auto">
      <HomeFeature {...props} />
    </div>
  );
}

function HomeFeatureDoubleColumn({
  features: [feature1, feature2],
  children,
}: {
  features: [Feature, Feature];
  children?: [React.ReactNode, React.ReactNode];
}): React.ReactNode {
  const [children1, children2] = children ?? [];

  return (
    <div className="grid gap-x-6 gap-y-8 grid-cols-1 lg:grid-cols-2 max-w-7xl px-4 py-8 md:px-16 mx-auto">
      <HomeFeature {...feature1}>{children1}</HomeFeature>
      <HomeFeature {...feature2}>{children2}</HomeFeature>
    </div>
  );
}

function HomeFeatures(): React.ReactNode {
  return (
    <>
      <HomeFeatureSingleColumn
        title="开箱即用"
        tagline="out of box"
        description="使用 NB-CLI 快速构建属于你的机器人"
      >
        <CodeBlock
          title="Installation"
          language="bash"
          className="home-codeblock"
        >
          {[
            "$ pipx install nb-cli",
            "$ nb",
            // "d8b   db  .d88b.  d8b   db d88888b d8888b.  .d88b.  d888888b",
            // "888o  88 .8P  Y8. 888o  88 88'     88  `8D .8P  Y8. `~~88~~'",
            // "88V8o 88 88    88 88V8o 88 88ooooo 88oooY' 88    88    88",
            // "88 V8o88 88    88 88 V8o88 88~~~~~ 88~~~b. 88    88    88",
            // "88  V888 `8b  d8' 88  V888 88.     88   8D `8b  d8'    88",
            // "VP   V8P  `Y88P'  VP   V8P Y88888P Y8888P'  `Y88P'     YP",
            "[?] What do you want to do?",
            "❯ Create a NoneBot project.",
            "  Run the bot in current folder.",
            "  Manage bot driver.",
            "  Manage bot adapters.",
            "  Manage bot plugins.",
            "  ...",
          ].join("\n")}
        </CodeBlock>
      </HomeFeatureSingleColumn>
      <HomeFeatureDoubleColumn
        features={[
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
        ]}
      >
        <CodeBlock title="" language="python" className="home-codeblock">
          {[
            "[project.entry-points.nb]",
            `plugin_name = "cli_plugin.plugin:install"`,
            "[project.entry-points.nb_scripts]",
            `foo = "awesome_bot.module:function"`,
            " ",
          ].join("\n")}
        </CodeBlock>
        <CodeBlock title="" language="python" className="home-codeblock">
          {[
            "[?] 你想要进行什么操作?",
            "❯ 创建一个 NoneBot 项目.",
            "  管理 bot 插件.",
            "  管理 bot 适配器.",
            "  管理 bot 驱动器.",
          ].join("\n")}
        </CodeBlock>
      </HomeFeatureDoubleColumn>
    </>
  );
}

export default React.memo(HomeFeatures);
