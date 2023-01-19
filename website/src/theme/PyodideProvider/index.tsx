import React from "react";
import type { PropsWithChildren } from "react";

import PyodideContext from "@theme/PyodideContext";
import usePyodide from "@theme/hooks/usePyodide";

function PyodideProvider(props: PropsWithChildren<unknown>): JSX.Element {
  const value = usePyodide();

  return (
    <PyodideContext.Provider value={value}>
      {props.children}
    </PyodideContext.Provider>
  );
}

export default PyodideProvider;
