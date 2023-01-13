import type { PyodideInterface } from "pyodide";
import React from "react";

export type PyodideContextType = {
  pyodide: PyodideInterface;
};

const PyodideContext = React.createContext<PyodideContextType | undefined>(
  undefined
);

export default PyodideContext;
