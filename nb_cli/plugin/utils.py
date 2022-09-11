from pathlib import Path


def path_to_module_name(path: Path) -> str:
    rel_path = path.resolve().relative_to(Path(".").resolve())
    if rel_path.stem == "__init__":
        return ".".join(rel_path.parts[:-1])
    else:
        return ".".join(rel_path.parts[:-1] + (rel_path.stem,))
