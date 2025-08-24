from pydantic import BaseModel

class Settings(BaseModel):
    app_name: str = "Quant Finance Platform API"

settings = Settings()
