import React, { useEffect, useState } from "react";

import CodeBlock from "@theme/CodeBlock";
import usePyodide from "@theme/hooks/usePyodide";

function RunPython({
  code,
  packages = [],
}: {
  code: string;
  packages?: string[];
}) {
  const [output, setOutput] = useState("正在加载 Python 模块...");
  const { pyodide, ensurePackage } = usePyodide();

  useEffect(() => {
    let isMounted = true;
    ensurePackage(packages).then(() => {
      pyodide.runPythonAsync(code).then((result) => {
        if (isMounted) {
          setOutput(result);
        }
      });
    });
    return () => {
      isMounted = false;
    };
  }, [code]);
  return <CodeBlock className="language-shell">{output}</CodeBlock>;
}

export default RunPython;
