from pydantic import BaseSettings
from functools import lru_cache
import urllib.parse
import os


class Settings(BaseSettings):
    # 数据库配置
    DB_HOST: str = "192.168.1.200"
    DB_PORT: int = 3306
    DB_USER: str = "eslsdb"
    DB_PASSWORD: str = "eslsdb@pi"
    DB_NAME: str = "db_centralcontrolmw"
    DB_CHARSET: str = "utf8mb4"
    DB_POOL_SIZE: int = 5
    DB_POOL_RECYCLE: int = 3600

    # TCP服务配置
    TCP_SERVER_HOST: str = "192.168.1.200"
    TCP_SERVER_PORT: int = 8080
    TCP_TIMEOUT: int = 5

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def DATABASE_URL(self) -> str:
        # 对密码进行URL编码，处理特殊字符
        encoded_password = urllib.parse.quote_plus(self.DB_PASSWORD)
        return f"mysql+pymysql://{self.DB_USER}:{encoded_password}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset={self.DB_CHARSET}"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
