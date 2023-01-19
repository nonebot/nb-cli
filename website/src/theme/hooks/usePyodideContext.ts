import { PyodideInterface } from "pyodide";
import { useContext } from "react";

import PyodideContext from "@theme/PyodideContext";

import type { usePyodideReturns } from "./usePyodide";

function usePyodideContext(): usePyodideReturns {
  const context = useContext<usePyodideReturns | undefined>(PyodideContext);
  if (context == null) {
    throw new Error(
      '"usePyodideContext" is used outside of "Layout" component.'
    );
  }
  return context;
}

export default usePyodideContext;
