from app.providers.base import BaseImageProvider
from app.providers.image2_provider import Image2Provider


def get_provider() -> BaseImageProvider:
    return Image2Provider()
