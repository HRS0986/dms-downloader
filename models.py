from pydantic import BaseModel
from typing import Optional, List


class ScraperConfig(BaseModel):
    url: str
    save_path: str


class ScrapedLink(BaseModel):
    filename: str
    url: str


class ScrapeProgress(BaseModel):
    current: int
    total: int
    filename: Optional[str] = None
    status: str
    links: Optional[List[ScrapedLink]] = None