import React, { useEffect, useState } from "react";

import CodeBlock from "@theme/CodeBlock";
import type { MockedPackage } from "@theme/hooks/usePyodide";
import usePyodideContext from "@theme/hooks/usePyodideContext";

function RunPython({
  code,
  placeholder = "Loading Python Modules...",
  packages = [],
  mockPackages = [],
  className = "",
}: {
  code: string;
  placeholder?: string;
  packages?: string[];
  mockPackages?: MockedPackage[];
  className?: string;
}) {
  const [output, setOutput] = useState(placeholder);
  const { pyodide, ensurePackage } = usePyodideContext();

  useEffect(() => {
    if (!pyodide) return;
    let isMounted = true;
    ensurePackage(packages, mockPackages).then(() => {
      pyodide.runPythonAsync(code).then((result) => {
        if (isMounted) {
          setOutput(result);
        }
      });
    });
    return () => {
      isMounted = false;
    };
  }, [code, packages, mockPackages, pyodide]);
  return <CodeBlock className={className}>{output}</CodeBlock>;
}

export default RunPython;
