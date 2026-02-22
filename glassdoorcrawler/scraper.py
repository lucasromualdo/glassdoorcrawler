import json
import logging
import time
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import progressbar
import requests
from bs4 import BeautifulSoup
from requests import Response

LOGGER = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"
    )
}


def _get(url: str, timeout: int = 20) -> Response:
    response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
    response.raise_for_status()
    return response


def _extract_page_state(body: Optional[BeautifulSoup]) -> Optional[Dict[str, Any]]:
    if body is None:
        return None

    for script in body.find_all("script"):
        text = script.get_text(strip=True)
        if not text or "initialState" not in text or "=" not in text:
            continue

        try:
            payload = text[text.index("=") + 1 :].rstrip(";")
            data = json.loads(payload)
            if isinstance(data, dict) and "initialState" in data:
                return data
        except (ValueError, json.JSONDecodeError):
            continue

    return None


def get_position_links(url: str) -> List[str]:
    """Collect job links from a single result page."""
    response = _get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    links: List[str] = []
    for anchor in soup.find_all("a", class_="jobLink"):
        href = anchor.get("href")
        if not href:
            continue
        if href.startswith("http"):
            links.append(href)
        else:
            links.append("https://www.glassdoor.com" + href)
    return links


def get_position_link(url: str) -> List[str]:
    """Backward-compatible alias kept for the old function name."""
    return get_position_links(url)


def _build_page_url(base_url: str, page: int) -> str:
    if page <= 1:
        return base_url

    if base_url.endswith(".htm"):
        return base_url[:-4] + f"_P{page}.htm"
    return f"{base_url}?page={page}"


def get_all_links(num_pages: int, base_url: str, delay_seconds: float = 0.5) -> List[List[str]]:
    """Collect job links across result pages."""
    all_links: List[List[str]] = []
    LOGGER.info("Collecting links...")

    for page in range(1, num_pages + 1):
        page_url = _build_page_url(base_url, page)
        try:
            all_links.append(get_position_links(page_url))
            time.sleep(delay_seconds)
        except requests.RequestException as exc:
            LOGGER.warning("Error collecting links from page %s (%s): %s", page, page_url, exc)
            break

    return all_links


def scrap_job_page(url: str) -> Dict[str, Any]:
    """Scrape a single job page."""
    result: Dict[str, Any] = {}
    response = _get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    body = soup.find("body")

    data = _extract_page_state(body)

    try:
        result["job_title"] = data["initialState"]["jlData"]["header"]["jobTitleText"] if data else np.nan
    except (KeyError, TypeError):
        result["job_title"] = np.nan

    try:
        result["company_name"] = data["initialState"]["jlData"]["header"]["employer"]["name"] if data else np.nan
    except (KeyError, TypeError):
        result["company_name"] = np.nan

    try:
        result["location"] = data["initialState"]["jlData"]["header"]["locationName"] if data else np.nan
    except (KeyError, TypeError):
        result["location"] = np.nan

    try:
        result["salary_estimated"] = body.find("h2", class_="salEst").text.strip() if body else np.nan
    except AttributeError:
        result["salary_estimated"] = np.nan

    try:
        result["salary_min"] = body.find("div", class_="minor cell alignLt").text.strip() if body else np.nan
    except AttributeError:
        result["salary_min"] = np.nan

    try:
        result["salary_max"] = body.find("div", class_="minor cell alignRt").text.strip() if body else np.nan
    except AttributeError:
        result["salary_max"] = np.nan

    try:
        result["job_description"] = data["initialState"]["jlData"]["job"]["description"] if data else np.nan
    except (KeyError, TypeError):
        result["job_description"] = np.nan

    return result


def crawl_jobs(
    base_url: str,
    num_pages: int = 1,
    output_path: str = "belohorizonte_vagas.xlsx",
    delay_seconds: float = 0.5,
) -> pd.DataFrame:
    """Run the crawl and save the results to an Excel file."""
    links = get_all_links(num_pages, base_url, delay_seconds=delay_seconds)
    flattened = [item for sublist in links for item in sublist]
    unique_links = list(dict.fromkeys(flattened))

    if not unique_links:
        LOGGER.warning("No job links found.")
        df_empty = pd.DataFrame()
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            df_empty.to_excel(writer, index=False)
        return df_empty

    bar = progressbar.ProgressBar(
        maxval=len(unique_links),
        widgets=[
            "Crawling the site: ",
            progressbar.Bar("=", "[", "]"),
            " ",
            progressbar.Percentage(),
        ],
    ).start()

    results: List[Dict[str, Any]] = []
    for index, page in enumerate(unique_links, start=1):
        bar.update(index)
        try:
            results.append(scrap_job_page(page))
        except requests.RequestException as exc:
            LOGGER.warning("Error scraping %s: %s", page, exc)
        except Exception as exc:  # pragma: no cover - defensive for unstable HTML
            LOGGER.warning("Unexpected parsing error in %s: %s", page, exc)
        time.sleep(delay_seconds)

    bar.finish()

    df_glass = pd.DataFrame.from_dict(results)
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df_glass.to_excel(writer, index=False)
    return df_glass
