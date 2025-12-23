import React from "react";

import Link from "@docusaurus/Link";
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { useNonepressThemeConfig } from "@nullbot/docusaurus-theme-nonepress/client";

function HomeHero(): React.ReactNode {
  const {
    siteConfig: { tagline },
  } = useDocusaurusContext();
  const {
    navbar: { logo },
  } = useNonepressThemeConfig();

  return (
    <div className="home-hero">
      <img src={logo!.src} alt={logo!.alt} className="home-hero-logo" />
      <h1 className="home-hero-title">
        <span className="text-primary">None</span>
        Bot CLI
      </h1>
      <p className="home-hero-tagline">{tagline}</p>
      <div className="home-hero-actions">
        <Link to="/docs/" className="btn btn-primary">
          开始使用 <FontAwesomeIcon icon={["fas", "chevron-right"]} />
        </Link>
      </div>
      <div className="home-hero-next">
        <FontAwesomeIcon icon={["fas", "angle-down"]} />
      </div>
    </div>
  );
}

export default React.memo(HomeHero);
