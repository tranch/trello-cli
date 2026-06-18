from pathlib import Path

from trello_cli.config import load_config_file, write_config


def test_load_config_file_returns_empty_dict_for_missing_file(tmp_path: Path) -> None:
    assert load_config_file(tmp_path / "missing.toml") == {}


def test_write_and_load_config_file(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"

    write_config("api-key", "token", config_path=config_path)

    assert load_config_file(config_path) == {"api_key": "api-key", "token": "token"}
    assert config_path.stat().st_mode & 0o777 == 0o600
