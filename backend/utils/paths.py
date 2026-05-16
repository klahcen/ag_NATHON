import os

_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_resolved_dir: str | None = None


def _is_writable(path: str) -> bool:
    test = os.path.join(path, ".write_test")
    try:
        with open(test, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(test)
        return True
    except OSError:
        return False


def get_data_dir() -> str:
    """Writable directory for JSON/CSV state. Prefers CURATOR_DATA_DIR, then data/, then storage/."""
    global _resolved_dir
    if _resolved_dir is not None:
        return _resolved_dir

    env = os.environ.get("CURATOR_DATA_DIR", "").strip()
    if env:
        path = os.path.abspath(env)
        os.makedirs(path, exist_ok=True)
        if not _is_writable(path):
            raise PermissionError(f"CURATOR_DATA_DIR is not writable: {path}")
        _resolved_dir = path
        return path

    for name in ("data", "storage"):
        path = os.path.join(_BACKEND_ROOT, name)
        os.makedirs(path, exist_ok=True)
        if _is_writable(path):
            _resolved_dir = path
            return path

    raise PermissionError(
        f"No writable data directory under {_BACKEND_ROOT}. "
        "Run: sudo chown -R $USER data/"
    )


def data_path(filename: str) -> str:
    return os.path.join(get_data_dir(), filename)
