import type { PyodideInterface } from "pyodide";
import React from "react";

import type { usePyodideReturns } from "./hooks/usePyodide";

const PyodideContext = React.createContext<usePyodideReturns | undefined>(
  undefined
);

export default PyodideContext;
