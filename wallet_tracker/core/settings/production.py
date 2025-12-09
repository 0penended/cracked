from wallet_tracker.core.settings.app import AppSettings


class ProdAppSettings(AppSettings):
    class Config(AppSettings.Config):
        env_file = ".env"
