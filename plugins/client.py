import os
from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import List, AsyncIterable

from aiohttp import ClientSession
from pathlib import Path

from bs4 import BeautifulSoup
from models import LastChapter
from tools import LanguageSingleton

async def check_links(link: str):
    #print(link)
    names = []
    urls = []
    i = 0
    useless = []
    while i > -5:
        url = f"{link}chapter-{i}/"
        async with ClientSession() as session:
            async with session.get(url) as response:
                html = await response.text()
                bs = BeautifulSoup(html, 'html.parser')
                container = bs.find("div", {"class" : "page-break no-gaps"})
                n = len(useless)
                if n > 3:
                    break
                if container: 
                    urls.append(url)
                    names.append(f"Chapter {i}")
                    i+=1
                elif not container:
                    useless.append(url)
                    i+=1
                     
    links = list(reversed(urls))
    texts = list(reversed(names))
    print(f" {len(urls)} : {len(texts)}")     
    return texts, links

@dataclass
class MangaCard:
    client: "MangaClient"
    name: str
    url: str
    picture_url: str

    def get_url(self):
        return self.url

    def unique(self):
        return str(hash(self.url))


@dataclass
class MangaChapter:
    client: "MangaClient"
    name: str
    url: str
    manga: MangaCard
    pictures: List[str]

    def get_url(self):
        return self.url

    def unique(self):
        return str(hash(self.url))


def clean(name, length=-1):
    while '  ' in name:
        name = name.replace('  ', ' ')
    name = name.replace(':', '')
    if length != -1:
        name = name[:length]
    return name


class MangaClient(ClientSession, metaclass=LanguageSingleton):
    
    def __init__(self, *args, name="client", **kwargs):
        if name == "client":
            raise NotImplementedError("A unique name must be provided for the client instance.")
        super().__init__(*args, **kwargs)
        self.name = name

    async def get_url(self, url, *args, file_name=None, cache=False, req_content=True, method='get', data=None,
                      headers=None, params=None, rjson=None, **kwargs):
        cache_path = Path(f'cache/{self.name}/{file_name}') if cache and file_name else None
        content = None

        # If caching is enabled and the cache file exists, load the content from the cache
        if cache and cache_path and cache_path.exists():
            with open(cache_path, 'rb') as f:
                content = f.read()
        else:
            # If no cache or cache miss, perform the network request
            response = await self._make_request(url, method, data, headers, params, *args, **kwargs)

            # Check if response is successful (2xx)
            if str(response.status).startswith('2'):
                content = await response.read()
                
                # Cache the content if caching is enabled
                if cache and cache_path:
                    cache_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(cache_path, 'wb') as f:
                        f.write(content)
            else:
                # Raise an error if the response is not successful
                raise RuntimeError(f"Request failed with status code: {response.status}")
            
            if rjson: return await response.json()
            elif req_content: return content
            else: return response

    async def _make_request(self, url, method, data, headers, params, *args, **kwargs):
        """Helper method to perform GET or POST requests."""
        if method == 'get':
            return await self.get(url, *args, headers=headers, params=params, **kwargs)
        elif method == 'post':
            return await self.post(url, data=data or {}, headers=headers, params=params, **kwargs)
        else:
            raise ValueError("Unsupported HTTP method")

    async def set_pictures(self, manga_chapter: MangaChapter):
        requests_url = manga_chapter.url

        response = await self.get(requests_url)

        content = await response.read()

        manga_chapter.pictures = await self.pictures_from_chapters(content, response)

        return manga_chapter

    async def download_pictures(self, manga_chapter: MangaChapter):
        if not manga_chapter.pictures:
            await self.set_pictures(manga_chapter)

        folder_name = f'{clean(manga_chapter.manga.name)}/{clean(manga_chapter.name)}'
        i = 0
        for picture in manga_chapter.pictures:
            ext = picture.split('.')[-1]
            file_name = f'{folder_name}/{format(i, "05d")}.{ext}'
            for _ in range(3):
                req = await self.get_picture(manga_chapter, picture, file_name=file_name, cache=True,
                                             req_content=False)
                if str(req.status).startswith('2'):
                    break
            else:
                raise ValueError
            i += 1

        return Path(f'cache/{manga_chapter.client.name}') / folder_name

    async def get_picture(self, manga_chapter: MangaChapter, url, *args, **kwargs):
        return await self.get_url(url, *args, **kwargs)

    async def get_cover(self, manga_card: MangaCard, *args, **kwargs):
        return await self.get_url(manga_card.picture_url, *args, **kwargs)

    async def check_updated_urls(self, last_chapters: List[LastChapter]):
        return [lc.url for lc in last_chapters], []

    @abstractmethod
    async def search(self, query: str = "", page: int = 1) -> List[MangaCard]:
        raise NotImplementedError

    @abstractmethod
    async def get_chapters(self, manga_card: MangaCard, page: int = 1) -> List[MangaChapter]:
        raise NotImplementedError

    @abstractmethod
    async def contains_url(self, url: str):
        raise NotImplementedError

    @abstractmethod
    async def iter_chapters(self, manga_url: str, manga_name: str) -> AsyncIterable[MangaChapter]:
        raise NotImplementedError

    @abstractmethod
    async def pictures_from_chapters(self, content: bytes, response=None):
        raise NotImplementedError
