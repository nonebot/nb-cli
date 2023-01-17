import { loadPyodide } from "pyodide";
import type {
  PyProxy,
  PyProxyCallable,
  PyProxyWithHas,
  PyodideInterface,
} from "pyodide";
import { useCallback, useEffect, useState } from "react";

interface Micropip extends PyProxy {
  install: (packageName: string | string[]) => Promise<void>;
  add_mock_package: PyProxyCallable;
  list_mock_packages: () => PyProxyWithHas;
  remove_mock_package: (name: string) => void;
}

export type MockedPackage = {
  name: string;
  version: string;
  modules?: Record<string, string>;
};

export type usePyodideReturns = {
  pyodide: PyodideInterface;
  ensurePackage: (
    packages?: string[],
    mockPackages?: MockedPackage[]
  ) => Promise<void>;
};

function usePyodide(): usePyodideReturns {
  const [pyodide, setPyodide] = useState<PyodideInterface | undefined>(
    undefined
  );

  useEffect(() => {
    loadPyodide({
      indexURL: "https://cdn.jsdelivr.net/pyodide/v0.22.0/full/",
    }).then(setPyodide);
  }, []);

  const ensurePackage = useCallback(
    async (packages: string[] = [], mockPackages: MockedPackage[] = []) => {
      const loadedPackages = Object.keys(pyodide.loadedPackages);
      const packagesToLoad = packages.filter(
        (p) => !loadedPackages.includes(p)
      );
      if (packagesToLoad.length === 0 && mockPackages.length === 0) {
        return;
      }
      await pyodide.loadPackage("micropip");
      const micropip = pyodide.pyimport("micropip") as Micropip;

      if (mockPackages.length > 0) {
        for (const mockPackage of mockPackages) {
          const mockedPackges = micropip.list_mock_packages();
          if (mockedPackges.has(mockPackage.name)) {
            micropip.remove_mock_package(mockPackage.name);
          }
          micropip.add_mock_package.callKwargs(
            mockPackage.name,
            mockPackage.version,
            { modules: mockPackage.modules }
          );
        }
      }
      if (packagesToLoad.length > 0) {
        await micropip.install(packagesToLoad);
      }

      micropip.destroy();
    },
    [pyodide]
  );

  return { pyodide, ensurePackage };
}

export default usePyodide;
