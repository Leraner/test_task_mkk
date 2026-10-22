from dishka import make_async_container

from src.shared.di.providers import get_providers_list

container = make_async_container(*get_providers_list())
