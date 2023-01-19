import React from "react";

import OriginProvider from "@theme-original/LayoutProviders";
import type { Props } from "@theme/LayoutProviders";
import PyodideProvider from "@theme/PyodideProvider";

function LayoutProvider(props: Props): JSX.Element {
  return (
    <PyodideProvider>
      <OriginProvider {...props} />
    </PyodideProvider>
  );
}

export default LayoutProvider;
