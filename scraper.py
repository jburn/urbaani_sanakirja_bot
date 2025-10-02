"""
Scraping functions for bot backend
"""
import aiohttp
from bs4 import BeautifulSoup
from scraper_constants import (
    BROWSE_ROOT_URL,
    BROWSE_TABS,
    ROOT_URL
)
from word_database import WordDatabase


async def fetch(session, url: str):
    """
    Fetch an url asynchronously
    """
    try:
        async with session.get(url, timeout=10) as r:
            if r.status != 200:
                return None
            return await r.text()
    except Exception:
        return None

def parse_votes(vote_str: str) -> int:
    """
    Parse votes from eg. 2,7k -> 2700 
    """
    vote_str = vote_str.lower().strip()
    if 'k' in vote_str:
        return int(float(vote_str.replace('k', '').replace(',', '.')) * 1000)
    else:
        return int(vote_str)

async def scan_for_links() -> list:
    """
    Scan for links to word definition pages
    """
    word_links = []
    async with aiohttp.ClientSession() as session:
        for tab in BROWSE_TABS:
            html = await fetch(session, BROWSE_ROOT_URL + tab)
            if not html:
                continue
            soup = BeautifulSoup(html, 'html.parser')
            links = soup.find_all('a')
            page_links = [int(l.get("href").split("=")[-1]) for l in links if l.get("href").startswith("?page=")]
            pages = 1
            if len(page_links) > 0:
                pages = max(page_links)
            for page in range(1, pages+1):
                page_html = await fetch(session, BROWSE_ROOT_URL + tab + f"/?page={page}")
                if not page_html:
                    continue
                psoup = BeautifulSoup(page_html, 'html.parser')
                wordl = psoup.find_all('a')
                words_to_add = [l.get("href") for l in wordl if l.get("href").startswith("/word/")]
                word_links.extend(words_to_add)
    return word_links

async def scan_for_words(links: list, db: WordDatabase):
    """
    Scan word definitions using a list of word page links
    """
    async with aiohttp.ClientSession() as session:
        for link in links:
            html = await fetch(session, ROOT_URL + link)
            if not html:
                continue
            soup = BeautifulSoup(html, "html.parser")
            boxes = soup.find_all('div', {"class": "box"})
            try:
                header = boxes[0].find("h1")
            except IndexError:
                continue
            title = header.text
            word = title.lower()
            for box in boxes:
                upvotes = box.find("button", {"class": "btn btn-vote-up rate-up"}).text.strip()
                downvotes = box.find("button", { "class": "btn btn-vote-down rate-down"}).text.strip()
                if parse_votes(upvotes) < parse_votes(downvotes):
                    continue
                explanation = box.find("p").text
                examples = "\n\n".join([quote.text.strip() for quote in box.find_all("blockquote")])
                user = box.find("span", {"class": "user"}).text
                date = box.find("span", {"class": "datetime"}).text
                labels = ", ".join([label.text.strip() for label in box.find_all(
                    "span",{"class": ["label label-positive", "label label-negative"]})
                    ])
                db.insert_definition((
                    word,
                    title,
                    explanation,
                    examples,
                    user,
                    date,
                    upvotes,
                    downvotes,
                    labels
                    ))

if __name__ == "__main__":
    import asyncio
    async def main():
        """
        main
        """
        database = WordDatabase()
        wlinks = await scan_for_links()
        await scan_for_words(wlinks, database)
        database.close()
    asyncio.run(main())
