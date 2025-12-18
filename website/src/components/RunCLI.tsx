import React from "react";

import RunPython from "./RunPython";

function RunCLI({
  code,
  placeholder = "Loading Python Modules...",
  className = "",
}: {
  code: string;
  placeholder?: string;
  className?: string;
}) {
  return (
    <RunPython
      code={code}
      placeholder={placeholder}
      packages={["ssl", "setuptools", "nb-cli"]}
      mockPackages={[
        {
          name: "watchfiles",
          version: "1.999.0",
          modules: new Map([
            ["watchfiles", "async def awatch(*args, **kwargs): ..."],
          ]),
        },
      ]}
      className={className}
    />
  );
}

export default RunCLI;
