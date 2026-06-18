import tomllib
from pathlib import Path

CONFIG_PATH = Path.home() / ".config" / "trello-cli" / "config.toml"


def load_config_file(config_path: Path = CONFIG_PATH) -> dict[str, str]:
    """Return Trello credentials from config.toml, or an empty dict."""
    if not config_path.exists():
        return {}

    try:
        with config_path.open("rb") as f:
            data = tomllib.load(f)
    except (tomllib.TOMLDecodeError, OSError):
        return {}

    section = data.get("trello", {})
    return {
        "api_key": section.get("api_key", ""),
        "token": section.get("token", ""),
    }


def write_config(api_key: str, token: str, config_path: Path = CONFIG_PATH) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        f'[trello]\napi_key = "{api_key}"\ntoken   = "{token}"\n',
        encoding="utf-8",
    )
    config_path.chmod(0o600)
