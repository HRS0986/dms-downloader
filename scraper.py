import requests
from bs4 import BeautifulSoup
import re
import tqdm
import asyncio
from typing import Dict, List, AsyncGenerator

from models import ScrapedLink


def extract_download_function(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    script_tags = soup.find_all('script')
    download_script = None
    for script in script_tags:
        if 'function download()' in str(script):
            download_script = str(script)
            break

    if not download_script:
        return None

    regex = r'(https://fuckingfast\.co/[^\s"\']+)'
    matches = re.findall(regex, download_script)
    return matches[0]


def scrape(fitgirl_link: str) -> list[dict[str, str]]:
    page_source = requests.get(fitgirl_link)
    soup = BeautifulSoup(page_source.text, 'html.parser')

    div = soup.find_all('div', {'class': 'su-spoiler-content su-u-clearfix su-u-trim'})
    anchor_tags = div[1].find_all('a')
    ffast_links = [link.get("href") for link in anchor_tags if "fucking" in link.get("href")]

    extracted_links = []
    print("Extracting download links...")
    p_bar = tqdm.tqdm(range(len(ffast_links)), desc="Processing", ncols=150)
    for i in p_bar:
        link = ffast_links[i]
        res = requests.get(link)
        filename = link.split("#")[1]
        p_bar.set_postfix_str(filename)
        download_link = extract_download_function(res.text)
        extracted_links.append({"filename":filename, "url":download_link})
    return extracted_links


async def scrape_with_progress(fitgirl_link: str) -> AsyncGenerator[Dict, None]:
    """Scrape links with progress updates sent as an async generator"""
    # Get the page source
    page_source = requests.get(fitgirl_link)
    soup = BeautifulSoup(page_source.text, 'html.parser')
    
    # Find all links
    div = soup.find_all('div', {'class': 'su-spoiler-content su-u-clearfix su-u-trim'})
    if not div or len(div) < 2:
        yield {
            "status": "error", 
            "message": "Could not find any download section on the page"
        }
        return
        
    anchor_tags = div[1].find_all('a')
    ffast_links = [link.get("href") for link in anchor_tags if "fucking" in link.get("href")]
    
    if not ffast_links:
        yield {
            "status": "error", 
            "message": "No download links found"
        }
        return
    
    # Initialize progress tracking
    total = len(ffast_links)
    extracted_links = []
    
    # Send initial progress update
    yield {
        "status": "started",
        "current": 0,
        "total": total,
        "message": "Starting to extract download links"
    }
    
    # Process each link with progress updates
    for i, link in enumerate(ffast_links):
        try:
            res = requests.get(link)
            filename = link.split("#")[1]
            
            # Send progress update
            yield {
                "status": "processing",
                "current": i + 1,
                "total": total,
                "filename": filename,
                "message": f"Processing {i + 1}/{total}: {filename}"
            }
            
            # Extract actual download link
            download_link = extract_download_function(res.text)
            
            if download_link:
                link_data = {"filename": filename, "url": download_link}
                extracted_links.append(link_data)
            
            # Small delay to prevent overwhelming the UI with updates
            await asyncio.sleep(0.1)
            
        except Exception as e:
            yield {
                "status": "error",
                "message": f"Error processing link {link}: {str(e)}",
                "current": i + 1,
                "total": total
            }
    
    # Send completion update with all extracted links
    yield {
        "status": "completed",
        "current": total,
        "total": total,
        "message": f"Completed extracting {len(extracted_links)} links",
        "links": extracted_links
    }


if __name__ == "__main__":
    url = "https://fitgirl-repacks.site/shadow-of-the-tomb-raider/"
    links = scrape(url)
    print(*links, sep="\n")