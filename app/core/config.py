from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_container_name: str
    db_container_name: str

    app_name: str
    environment: str
    debug: bool
    api_v1_prefix: str
    auto_create_tables: bool

    app_port: int
    db_port: int

    postgres_user: str
    postgres_password: str
    postgres_db: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @staticmethod
    def _error_page(title: str, heading: str) -> str:
        return f"""
        <!doctype html>
        <html>
            <head>
                <title>{title}</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <link rel="icon" type="image/x-icon" href="/static/images/favicon.ico">
            </head>
            <body>
                <h1 style="color: #E63F31">{heading}</h1>
            </body>
        </html>"""

    @property
    def not_found(self) -> str:
        return self._error_page("404 - Page not found", "404 - Page not found")

    @property
    def method_not_allowed(self) -> str:
        return self._error_page("405 - Method not allowed", "405 - Method not allowed")

    def custom_error(self, exc_status_code: int) -> str:
        return self._error_page(f"Error {exc_status_code}", f"Error {exc_status_code}")

    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://"
            f"{self.postgres_user}:"
            f"{self.postgres_password}@"
            f"localhost:"
            f"{self.db_port}/"
            f"{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
