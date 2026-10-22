from src.shared.web.api_settings import get_api_settings
from src.shared.web.application import Application

if __name__ == "__main__":
    Application(get_api_settings()).run()
