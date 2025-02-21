from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "mysql+pymysql://voting_user:voting_pass@db:3306/voting_db"
    
settings = Settings() 