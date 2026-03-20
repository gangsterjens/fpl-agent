from pydantic import BaseSettings

class Settings(BaseSettings):
    sb_pw: str
    yt_api_key: str
    sb_url: str
    sb_api_key: str
    google_oauth_client_id: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

