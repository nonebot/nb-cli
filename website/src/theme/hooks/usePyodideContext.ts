import { PyodideInterface } from "pyodide";
import { useContext } from "react";

import type { PyodideContextType } from "@theme/PyodideContext";
import PyodideContext from "@theme/PyodideContext";

function usePyodideContext(): PyodideContextType {
  const context = useContext<PyodideContextType | undefined>(PyodideContext);
  if (context == null) {
    throw new Error(
      '"usePyodideContext" is used outside of "Layout" component.'
    );
  }
  return context;
}

export default usePyodideContext;
