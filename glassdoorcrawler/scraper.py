import json
import logging
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import numpy as np
import pandas as pd
import progressbar
import requests
from bs4 import BeautifulSoup
from requests import Response, Session

LOGGER = logging.getLogger(__name__)

try:
    from curl_cffi import requests as curl_requests
except ImportError:  # pragma: no cover - optional runtime dependency
    curl_requests = None

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}

FALLBACK_IMPERSONATE_PROFILES = ("chrome124", "safari184")


class _HttpClient:
    """HTTP client with optional Cloudflare fallback via curl_cffi."""

    def __init__(self, use_env_proxies: bool = True):
        self._use_env_proxies = use_env_proxies
        self._requests_session = requests.Session()
        self._requests_session.trust_env = use_env_proxies
        self._curl_session = None
        self._prefer_curl = False

    def _is_cloudflare_security_page(self, response: Any) -> bool:
        text = getattr(response, "text", "") or ""
        server = (getattr(response, "headers", {}) or {}).get("server", "")
        status_code = getattr(response, "status_code", None)
        return (
            status_code == 403
            and "cloudflare" in str(server).lower()
            and "Security | Glassdoor" in text
        )

    def _curl_proxies(self) -> Optional[Dict[str, str]]:
        if self._use_env_proxies:
            return None
        # curl_cffi still reads env proxies in some cases unless explicitly overridden.
        return {"http": "", "https": ""}

    def _ensure_curl_session(self) -> Any:
        if curl_requests is None:
            raise RuntimeError("curl_cffi is not installed")
        if self._curl_session is None:
            self._curl_session = curl_requests.Session()
        return self._curl_session

    def _get_with_curl(self, url: str, timeout: int, headers: Dict[str, str]) -> Any:
        last_response = None
        session = self._ensure_curl_session()
        proxies = self._curl_proxies()

        for profile in FALLBACK_IMPERSONATE_PROFILES:
            kwargs: Dict[str, Any] = {
                "headers": headers,
                "timeout": timeout,
                "impersonate": profile,
            }
            if proxies is not None:
                kwargs["proxies"] = proxies

            response = session.get(url, **kwargs)
            last_response = response
            if response.status_code < 400 or not self._is_cloudflare_security_page(response):
                if not self._prefer_curl:
                    LOGGER.info("Enabled curl_cffi fallback transport (%s) after Cloudflare block.", profile)
                self._prefer_curl = True
                return response

        return last_response

    def get(self, url: str, headers: Dict[str, str], timeout: int) -> Any:
        if self._prefer_curl and curl_requests is not None:
            return self._get_with_curl(url, timeout=timeout, headers=headers)

        response = self._requests_session.get(url, headers=headers, timeout=timeout)
        if self._is_cloudflare_security_page(response) and curl_requests is not None:
            LOGGER.warning("Cloudflare security page detected for %s; retrying with curl_cffi.", url)
            return self._get_with_curl(url, timeout=timeout, headers=headers)
        return response

    def close(self) -> None:
        self._requests_session.close()
        if self._curl_session is not None:
            try:
                self._curl_session.close()
            except Exception:  # pragma: no cover - defensive cleanup
                pass


def _build_session(use_env_proxies: bool = True) -> _HttpClient:
    return _HttpClient(use_env_proxies=use_env_proxies)


def _get(
    url: str,
    timeout: int = 20,
    session: Optional[Any] = None,
) -> Any:
    client = session or requests
    response = client.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
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


def _extract_job_posting_jsonld(soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
    for script in soup.find_all("script", type="application/ld+json"):
        text = script.get_text(strip=True)
        if not text:
            continue

        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            continue

        items = payload if isinstance(payload, list) else [payload]
        for item in items:
            if isinstance(item, dict) and item.get("@type") == "JobPosting":
                return item

    return None


def _normalize_job_link(href: str) -> str:
    if href.startswith("http"):
        return href
    return "https://www.glassdoor.com" + href


def _is_job_listing_href(href: str) -> bool:
    parsed = urlparse(href)
    path = parsed.path if parsed.scheme else href
    return "/job-listing/" in path.lower()


def _extract_location_from_job_posting(job_posting: Dict[str, Any]) -> Any:
    location = job_posting.get("jobLocation")
    if not location:
        return np.nan

    location_items = location if isinstance(location, list) else [location]
    formatted_locations: List[str] = []

    for item in location_items:
        if not isinstance(item, dict):
            continue
        address = item.get("address", {})
        if not isinstance(address, dict):
            continue

        parts = [
            str(address.get("addressLocality", "")).strip(),
            str(address.get("addressRegion", "")).strip(),
        ]
        joined = ", ".join([part for part in parts if part])
        if joined:
            formatted_locations.append(joined)

    if not formatted_locations:
        return np.nan

    return " | ".join(dict.fromkeys(formatted_locations))


def _extract_salary_fields_from_job_posting(job_posting: Dict[str, Any]) -> Dict[str, Any]:
    base_salary = job_posting.get("baseSalary")
    if not isinstance(base_salary, dict):
        return {
            "salary_estimated": np.nan,
            "salary_min": np.nan,
            "salary_max": np.nan,
        }

    value = base_salary.get("value", {})
    currency = job_posting.get("salaryCurrency", "")
    if not isinstance(value, dict):
        return {
            "salary_estimated": np.nan,
            "salary_min": np.nan,
            "salary_max": np.nan,
        }

    min_value = value.get("minValue", np.nan)
    max_value = value.get("maxValue", np.nan)
    exact_value = value.get("value", np.nan)

    salary_estimated = exact_value
    if isinstance(exact_value, (int, float)) and currency:
        salary_estimated = f"{currency} {exact_value}"

    return {
        "salary_estimated": salary_estimated if salary_estimated == salary_estimated else np.nan,
        "salary_min": min_value if min_value == min_value else np.nan,
        "salary_max": max_value if max_value == max_value else np.nan,
    }


def get_position_links(url: str, session: Optional[Any] = None) -> List[str]:
    """Collect job links from a single result page."""
    response = _get(url, session=session)
    soup = BeautifulSoup(response.text, "html.parser")

    links: List[str] = []

    # Legacy selector kept for backward compatibility (older Glassdoor markup).
    for anchor in soup.find_all("a", class_="jobLink"):
        href = anchor.get("href")
        if href and _is_job_listing_href(href):
            links.append(_normalize_job_link(href))

    # Fallback for current markup: scan all anchors and keep canonical job-listing URLs.
    if not links:
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]
            if _is_job_listing_href(href):
                links.append(_normalize_job_link(href))

    return list(dict.fromkeys(links))


def get_position_link(url: str) -> List[str]:
    """Backward-compatible alias kept for the old function name."""
    return get_position_links(url)


def _build_page_url(base_url: str, page: int) -> str:
    if page <= 1:
        return base_url

    if base_url.endswith(".htm"):
        return base_url[:-4] + f"_P{page}.htm"
    return f"{base_url}?page={page}"


def get_all_links(
    num_pages: int,
    base_url: str,
    delay_seconds: float = 0.5,
    session: Optional[Any] = None,
) -> List[List[str]]:
    """Collect job links across result pages."""
    all_links: List[List[str]] = []
    LOGGER.info("Collecting links...")

    for page in range(1, num_pages + 1):
        page_url = _build_page_url(base_url, page)
        try:
            all_links.append(get_position_links(page_url, session=session))
            time.sleep(delay_seconds)
        except requests.RequestException as exc:
            LOGGER.warning("Error collecting links from page %s (%s): %s", page, page_url, exc)
            break

    return all_links


def scrap_job_page(url: str, session: Optional[Any] = None) -> Dict[str, Any]:
    """Scrape a single job page."""
    result: Dict[str, Any] = {}
    response = _get(url, session=session)
    soup = BeautifulSoup(response.text, "html.parser")
    body = soup.find("body")

    data = _extract_page_state(body)
    job_posting = _extract_job_posting_jsonld(soup)

    try:
        if data:
            result["job_title"] = data["initialState"]["jlData"]["header"]["jobTitleText"]
        elif job_posting:
            result["job_title"] = job_posting.get("title", np.nan)
        else:
            result["job_title"] = np.nan
    except (KeyError, TypeError):
        result["job_title"] = np.nan

    try:
        if data:
            result["company_name"] = data["initialState"]["jlData"]["header"]["employer"]["name"]
        elif job_posting:
            employer = job_posting.get("hiringOrganization", {})
            result["company_name"] = employer.get("name", np.nan) if isinstance(employer, dict) else np.nan
        else:
            result["company_name"] = np.nan
    except (KeyError, TypeError):
        result["company_name"] = np.nan

    try:
        if data:
            result["location"] = data["initialState"]["jlData"]["header"]["locationName"]
        elif job_posting:
            result["location"] = _extract_location_from_job_posting(job_posting)
        else:
            result["location"] = np.nan
    except (KeyError, TypeError):
        result["location"] = np.nan

    try:
        result["salary_estimated"] = body.find("h2", class_="salEst").text.strip() if body else np.nan
    except AttributeError:
        if job_posting:
            result["salary_estimated"] = _extract_salary_fields_from_job_posting(job_posting)[
                "salary_estimated"
            ]
        else:
            result["salary_estimated"] = np.nan

    try:
        result["salary_min"] = body.find("div", class_="minor cell alignLt").text.strip() if body else np.nan
    except AttributeError:
        if job_posting:
            result["salary_min"] = _extract_salary_fields_from_job_posting(job_posting)["salary_min"]
        else:
            result["salary_min"] = np.nan

    try:
        result["salary_max"] = body.find("div", class_="minor cell alignRt").text.strip() if body else np.nan
    except AttributeError:
        if job_posting:
            result["salary_max"] = _extract_salary_fields_from_job_posting(job_posting)["salary_max"]
        else:
            result["salary_max"] = np.nan

    try:
        if data:
            result["job_description"] = data["initialState"]["jlData"]["job"]["description"]
        elif job_posting:
            result["job_description"] = job_posting.get("description", np.nan)
        else:
            result["job_description"] = np.nan
    except (KeyError, TypeError):
        result["job_description"] = np.nan

    return result


def crawl_jobs(
    base_url: str,
    num_pages: int = 1,
    output_path: str = "belohorizonte_vagas.xlsx",
    delay_seconds: float = 0.5,
    use_env_proxies: bool = True,
) -> pd.DataFrame:
    """Run the crawl and save the results to an Excel file."""
    session = _build_session(use_env_proxies=use_env_proxies)
    try:
        links = get_all_links(num_pages, base_url, delay_seconds=delay_seconds, session=session)
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
                results.append(scrap_job_page(page, session=session))
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
    finally:
        session.close()
