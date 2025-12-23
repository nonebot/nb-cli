import { themes } from "prism-react-renderer";

import type * as Preset from "@nullbot/docusaurus-preset-nonepress";

// color mode config
const colorMode: Preset.ThemeConfig["colorMode"] = {
  defaultMode: "light",
  respectPrefersColorScheme: true,
};

// navbar config
const navbar: Preset.ThemeConfig["navbar"] = {
  title: "NoneBot CLI",
  logo: {
    alt: "NoneBot CLI",
    src: "logo.png",
    href: "/",
    target: "_self",
    height: 32,
    width: 32,
  },

  hideOnScroll: false,
  items: [
    {
      label: "指南",
      type: "docsMenu",
      category: "guide",
    },
    {
      label: "API",
      type: "doc",
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
};

// footer config
const footer: Preset.ThemeConfig["footer"] = {
  style: "light",
  copyright: `Copyright © ${new Date().getFullYear()} NoneBot. All rights reserved.`,
  links: [
    {
      title: "Learn",
      items: [
        { label: "介绍", to: "/docs/" },
        { label: "安装", to: "/docs/guide/installation" },
      ],
    },
    {
      title: "NoneBot Team",
      items: [
        {
          label: "NoneBot V1",
          href: "https://v1.nonebot.dev",
        },
        { label: "NoneBot V2", href: "https://nonebot.dev" },
      ],
    },
  ],
};

// prism config
const lightCodeTheme = themes.github;
const darkCodeTheme = themes.dracula;

const prism: Preset.ThemeConfig["prism"] = {
  theme: lightCodeTheme,
  darkTheme: darkCodeTheme,
  additionalLanguages: ["docker", "toml"],
};

// nonepress config
const nonepress: Preset.ThemeConfig["nonepress"] = {
  tailwindConfig: require("./tailwind.config"),
  navbar: {
    docsVersionDropdown: {
      dropdownItemsAfter: [
        {
          label: "1.x",
          href: "https://v1.nonebot.dev/",
        },
      ],
    },
    socialLinks: [
      {
        icon: ["fab", "github"],
        href: "https://github.com/nonebot/nonebot2",
      },
    ],
  },
  footer: {
    socialLinks: [
      {
        icon: ["fab", "github"],
        href: "https://github.com/nonebot/nonebot2",
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
  },
};

const themeConfig: Preset.ThemeConfig = {
  colorMode,
  navbar,
  footer,
  prism,
  nonepress,
};

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
      "@nullbot/docusaurus-preset-nonepress",
      {
        docs: {
          sidebarPath: require.resolve("./sidebars.js"),
          editUrl: "https://github.com/nonebot/nb-cli/edit/master/website/",
          showLastUpdateAuthor: true,
          showLastUpdateTime: true,
        },
      },
    ],
  ],

  future: {
    experimental_faster: true,
    v4: true,
  },

  plugins: [require("./src/plugins/webpack-plugin.ts")],

  markdown: {
    mdx1Compat: {
      headingIds: true,
    },
  },

  themeConfig,
};

export default config;
