import { loadPyodide } from "pyodide";
import type { PyProxy, PyodideInterface } from "pyodide";
import { useCallback, useEffect, useState } from "react";

interface Micropip extends PyProxy {
  install: (packageName: string | string[]) => Promise<void>;
  destroy: () => void;
}

export type usePyodideReturns = {
  pyodide: PyodideInterface;
  ensurePackage: (packages: string[]) => Promise<void>;
};

function usePyodide(): usePyodideReturns {
  const [pyodide, setPyodide] = useState<PyodideInterface | undefined>(
    undefined
  );

  useEffect(() => {
    loadPyodide().then(setPyodide);
  }, []);

  const ensurePackage = useCallback(
    async (packages: string[] = []) => {
      const loadedPackages = Object.keys(pyodide.loadedPackages);
      const packagesToLoad = packages.filter(
        (p) => !loadedPackages.includes(p)
      );
      if (packagesToLoad.length === 0) {
        return;
      }
      await pyodide.loadPackage("micropip");
      const micropip = pyodide.pyimport("micropip") as Micropip;
      await micropip.install(packagesToLoad);
      micropip.destroy();
    },
    [pyodide]
  );

  return { pyodide, ensurePackage };
}

export default usePyodide;
