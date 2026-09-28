import yaml
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict, PydanticBaseSettingsSource
from typing import List, Dict, Any, Tuple


class YamlConfigSettingsSource(PydanticBaseSettingsSource):
    def __init__(self, settings_cls: type[BaseSettings], yaml_file: str = "config.yaml"):
        super().__init__(settings_cls)
        self.yaml_file = Path(yaml_file)
        self._data = self._load_yaml()

    def _load_yaml(self) -> Dict[str, Any]:
        if self.yaml_file.exists():
            with open(self.yaml_file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

    def get_field_value(self, field, field_name):
        keys = field_name.split(".")
        value = self._data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value

    def prepare_field_value(self, field_name, field, value, value_is_complex):
        return value

    def __call__(self) -> Dict[str, Any]:
        return self._data


class UnorouterSettings(BaseSettings):
    base_url: str = "https://api.unorouter.com"

    model_config = SettingsConfigDict(extra="ignore")


class CacheSettings(BaseSettings):
    default_ttl_seconds: int = 900
    catalog_ttl_seconds: int = 900
    model_ttl_seconds: int = 900
    counts_ttl_seconds: int = 300
    vendors_ttl_seconds: int = 3600

    model_config = SettingsConfigDict(extra="ignore")


class TrackedModelsSettings(BaseSettings):
    tracked_models: List[str] = Field(default=["glm-5.3"])

    model_config = SettingsConfigDict(extra="ignore", populate_by_name=True)


class ServerSettings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 7414

    model_config = SettingsConfigDict(extra="ignore")


class DatabaseSettings(BaseSettings):
    path: str = "pricing_cache.db"

    model_config = SettingsConfigDict(extra="ignore")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        extra="ignore",
    )

    unorouter: UnorouterSettings = UnorouterSettings()
    cache: CacheSettings = CacheSettings()
    tracked_models: TrackedModelsSettings = TrackedModelsSettings()
    server: ServerSettings = ServerSettings()
    database: DatabaseSettings = DatabaseSettings()

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            YamlConfigSettingsSource(settings_cls, "config.yaml"),
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )


settings = Settings()