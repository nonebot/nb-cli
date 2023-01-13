// @ts-check

const lightCodeTheme = require("prism-react-renderer/themes/github");
const darkCodeTheme = require("prism-react-renderer/themes/dracula");

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: "NoneBot",
  tagline: "CLI for NoneBot 2",
  url: "https://cli.nonebot.dev/",
  baseUrl: "/",
  onBrokenLinks: "throw",
  onBrokenMarkdownLinks: "warn",
  favicon: "img/favicon.ico",
  organizationName: "nonebot",
  projectName: "nb-cli",
  i18n: {
    defaultLocale: "zh-Hans",
    locales: ["zh-Hans"],
    localeConfigs: {
      "zh-Hans": { label: "简体中文" },
    },
  },

  presets: [
    [
      "docusaurus-preset-nonepress",
      /** @type {import('docusaurus-preset-nonepress').Options} */
      ({
        docs: {
          sidebarPath: require.resolve("./sidebars.js"),
          editUrl: "https://github.com/nonebot/nb-cli/edit/master/website/",
          showLastUpdateAuthor: true,
          showLastUpdateTime: true,
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('docusaurus-preset-nonepress').ThemeConfig} */
    ({
      colorMode: {
        defaultMode: "light",
      },
      logo: {
        alt: "",
        src: "logo.png",
        href: "/",
        target: "_self",
      },
      navbar: {
        hideOnScroll: true,
        items: [
          {
            label: "指南",
            type: "docsMenu",
            category: "guide",
          },
          {
            label: "API",
            type: "docLink",
            docId: "api/index",
          },
          {
            label: "NoneBot",
            icon: ["fas", "angle-double-right"],
            href: "https://github.com/nonebot/nonebot2",
          },
          {
            icon: ["fab", "github"],
            href: "https://github.com/nonebot/nb-cli",
          },
        ],
      },
      hideableSidebar: true,
      footer: {
        copyright: `Copyright © ${new Date().getFullYear()} NoneBot. All rights reserved.`,
        iconLinks: [
          {
            icon: ["fab", "github"],
            href: "https://github.com/nonebot/nb-cli",
            description: "GitHub",
          },
          {
            icon: ["fab", "qq"],
            href: "https://jq.qq.com/?_wv=1027&k=5OFifDh",
          },
          {
            icon: ["fab", "telegram"],
            href: "https://t.me/botuniverse",
          },
          {
            icon: ["fab", "discord"],
            href: "https://discord.gg/VKtE6Gdc4h",
          },
        ],
        links: [
          {
            title: "Learn",
            icon: ["fas", "book"],
            items: [
              { label: "介绍", to: "/docs/" },
              { label: "安装", to: "/docs/guide/installation" },
            ],
          },
          {
            title: "NoneBot Team",
            icon: ["fas", "user-friends"],
            items: [
              {
                label: "主页",
                href: "https://nonebot.dev",
              },
              {
                label: "NoneBot V1",
                href: "https://docs.nonebot.dev",
              },
              { label: "NoneBot V2", href: "https://v2.nonebot.dev" },
            ],
          },
        ],
      },
      prism: {
        theme: lightCodeTheme,
        darkTheme: darkCodeTheme,
        additionalLanguages: ["toml"],
      },
      algolia: {
        appId: "<empty>",
        apiKey: "<empty>",
        indexName: "<empty>",
        contextualSearch: true,
      },
      tailwindConfig: require("./tailwind.config"),
    }),
};

module.exports = config;
