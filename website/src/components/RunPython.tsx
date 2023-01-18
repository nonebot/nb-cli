import React, { useEffect, useState } from "react";

import CodeBlock from "@theme/CodeBlock";
import usePyodide from "@theme/hooks/usePyodide";
import type { MockedPackage } from "@theme/hooks/usePyodide";

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
  const { pyodide, ensurePackage } = usePyodide();

  useEffect(() => {
    if (!pyodide) return;
    let isMounted = true;
    ensurePackage(packages, mockPackages).then(() => {
      console.log(code, isMounted);
      pyodide.runPythonAsync(code).then((result) => {
        console.log(isMounted, result);
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
