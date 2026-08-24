from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    GROQ_API_KEY: str = ""
    HUGGINGFACE_API_KEY: str = ""
    
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 150
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def update(self, groq_key: str = None, huggingface_key: str = None):
        if groq_key:
            self.GROQ_API_KEY = groq_key
        if huggingface_key:
            self.HUGGINGFACE_API_KEY = huggingface_key

settings = Settings()
