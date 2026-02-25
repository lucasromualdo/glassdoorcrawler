import json
import logging
import re
import time
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

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
JOB_SEARCH_RESULTS_BFF_URL = "https://www.glassdoor.com.br/job-search-next/bff/jobSearchResultsQuery"


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

    def _request_with_curl(
        self,
        method: str,
        url: str,
        timeout: int,
        headers: Dict[str, str],
        json_payload: Optional[Dict[str, Any]] = None,
    ) -> Any:
        last_response = None
        session = self._ensure_curl_session()
        proxies = self._curl_proxies()

        for profile in FALLBACK_IMPERSONATE_PROFILES:
            kwargs: Dict[str, Any] = {
                "headers": headers,
                "timeout": timeout,
                "impersonate": profile,
            }
            if json_payload is not None:
                kwargs["json"] = json_payload
            if proxies is not None:
                kwargs["proxies"] = proxies

            response = session.request(method, url, **kwargs)
            last_response = response
            if response.status_code < 400 or not self._is_cloudflare_security_page(response):
                if not self._prefer_curl:
                    LOGGER.info("Enabled curl_cffi fallback transport (%s) after Cloudflare block.", profile)
                self._prefer_curl = True
                return response

        return last_response

    def _request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        timeout: int,
        json_payload: Optional[Dict[str, Any]] = None,
    ) -> Any:
        if self._prefer_curl and curl_requests is not None:
            return self._request_with_curl(
                method,
                url,
                timeout=timeout,
                headers=headers,
                json_payload=json_payload,
            )

        response = self._requests_session.request(
            method,
            url,
            headers=headers,
            timeout=timeout,
            json=json_payload,
        )
        if self._is_cloudflare_security_page(response) and curl_requests is not None:
            LOGGER.warning("Cloudflare security page detected for %s; retrying with curl_cffi.", url)
            return self._request_with_curl(
                method,
                url,
                timeout=timeout,
                headers=headers,
                json_payload=json_payload,
            )
        return response

    def get(self, url: str, headers: Dict[str, str], timeout: int) -> Any:
        return self._request("GET", url, headers=headers, timeout=timeout)

    def post(
        self,
        url: str,
        headers: Dict[str, str],
        timeout: int,
        json_payload: Dict[str, Any],
    ) -> Any:
        return self._request(
            "POST",
            url,
            headers=headers,
            timeout=timeout,
            json_payload=json_payload,
        )

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


def _extract_next_flight_decoded_payload(soup: BeautifulSoup) -> Optional[str]:
    for script in soup.find_all("script"):
        text = script.string or script.get_text() or ""
        if "paginationCursors" not in text or "self.__next_f.push" not in text:
            continue

        match = re.search(r'self\.__next_f\.push\(\[1,\"(.*)\"\]\)\s*$', text, re.S)
        if not match:
            continue

        try:
            return json.loads(f'"{match.group(1)}"')
        except json.JSONDecodeError:
            continue

    return None


def _map_location_type_for_bff(location_type: str) -> str:
    return {
        "C": "CITY",
        "S": "STATE",
        "N": "NATION",
        "M": "METRO",
    }.get(location_type, location_type)


def _extract_search_bootstrap_for_pagination(soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
    decoded = _extract_next_flight_decoded_payload(soup)
    if not decoded:
        return None

    def _match(pattern: str) -> Optional[str]:
        match = re.search(pattern, decoded, re.S)
        return match.group(1) if match else None

    filter_params_match = re.search(
        r'"queryString":"[^"]*","filterParams":(\[[\s\S]*?\]),"searchUrlParams":',
        decoded,
        re.S,
    )
    try:
        filter_params = json.loads(filter_params_match.group(1)) if filter_params_match else []
    except json.JSONDecodeError:
        filter_params = []

    pagination_cursors = {
        int(page_number): cursor
        for cursor, page_number in re.findall(r'{"cursor":"([^"]+)","pageNumber":(\d+)}', decoded)
        if int(page_number) >= 2
    }
    if not pagination_cursors:
        return None

    location_id_raw = _match(r'"locationId":"?(\d+)"?')
    location_type_raw = _match(r'"locationType":"([A-Z])"') or ""
    job_listing_id_from_url_raw = _match(r'"jobListingIdFromUrl":(\d+)')

    return {
        "absolute_url": _match(r'"searchContext":\{"absoluteUrl":"([^"]+)"') or "",
        "query_string": _match(r'"queryString":"([^"]*)","filterParams"') or "",
        "filter_params": filter_params,
        "is_logged_in": (_match(r'"isLoggedIn":(true|false)') == "true"),
        "job_listing_id_from_url": int(job_listing_id_from_url_raw or "0"),
        "keyword": _match(r'"occupationParam":"([^"]*)"') or "",
        "location_id": int(location_id_raw or "0"),
        "location_type": _map_location_type_for_bff(location_type_raw),
        "parameter_url_input": _match(r'"parameterUrlInput":"([^"]+)"') or "",
        "seo_friendly_url_input": _match(r'"seoFriendlyUrlInput":"([^"]+)"') or "",
        "seo_url": (_match(r'"seoUrl":(true|false)') == "true"),
        "pagination_cursors": pagination_cursors,
    }


def _extract_job_links_from_search_soup(soup: BeautifulSoup) -> List[str]:
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


def _get_search_page_links_and_bootstrap(
    url: str,
    session: Optional[Any] = None,
) -> tuple[List[str], Optional[Dict[str, Any]]]:
    response = _get(url, session=session)
    soup = BeautifulSoup(response.text, "html.parser")
    return _extract_job_links_from_search_soup(soup), _extract_search_bootstrap_for_pagination(soup)


def _get_links_from_bff_page(
    page_number: int,
    bootstrap: Dict[str, Any],
    session: Optional[Any] = None,
    timeout: int = 20,
) -> List[str]:
    page_cursor = (bootstrap.get("pagination_cursors") or {}).get(page_number)
    if not page_cursor:
        return []

    payload = {
        "excludeJobListingIds": (
            [bootstrap["job_listing_id_from_url"]] if bootstrap.get("job_listing_id_from_url") else []
        ),
        "filterParams": bootstrap.get("filter_params", []),
        "includeIndeedJobAttributes": not bootstrap.get("is_logged_in", False),
        "keyword": bootstrap.get("keyword", ""),
        "locationId": bootstrap.get("location_id", 0),
        "locationType": bootstrap.get("location_type", ""),
        "numJobsToShow": 30,
        "originalPageUrl": bootstrap.get("absolute_url", ""),
        "pageCursor": page_cursor,
        "pageNumber": page_number,
        "pageType": "SERP",
        "parameterUrlInput": bootstrap.get("parameter_url_input", ""),
        "queryString": bootstrap.get("query_string", ""),
        "seoFriendlyUrlInput": bootstrap.get("seo_friendly_url_input", ""),
        "seoUrl": bootstrap.get("seo_url", True),
    }

    headers = {
        **DEFAULT_HEADERS,
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
    }

    if session is not None and hasattr(session, "post"):
        response = session.post(
            JOB_SEARCH_RESULTS_BFF_URL,
            headers=headers,
            timeout=timeout,
            json_payload=payload,
        )
    else:
        response = requests.post(
            JOB_SEARCH_RESULTS_BFF_URL,
            headers=headers,
            timeout=timeout,
            json=payload,
        )
    response.raise_for_status()

    body = response.json()
    data_section = body.get("data", body) if isinstance(body, dict) else {}
    job_listings_section = (data_section or {}).get("jobListings", {})
    items = job_listings_section.get("jobListings", []) if isinstance(job_listings_section, dict) else []

    links: List[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        header = ((item.get("jobview") or {}).get("header") or {})
        seo_link = header.get("seoJobLink")
        if isinstance(seo_link, str) and seo_link:
            links.append(_normalize_job_link(seo_link))

    return list(dict.fromkeys(links))


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
    return _extract_job_links_from_search_soup(soup)


def get_position_link(url: str) -> List[str]:
    """Backward-compatible alias kept for the old function name."""
    return get_position_links(url)


def _build_page_url(base_url: str, page: int) -> str:
    if page <= 1:
        return base_url

    if base_url.endswith(".htm"):
        return base_url[:-4] + f"_P{page}.htm"
    return f"{base_url}?page={page}"


def _replace_query_param(url: str, key: str, value: Any) -> str:
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query[key] = str(value)
    return urlunparse(parsed._replace(query=urlencode(query)))


def _build_page_url_candidates(base_url: str, page: int) -> List[str]:
    if page <= 1:
        return [base_url]

    candidates: List[str] = []

    # Current Jobs Next pages often react to query-based pagination in SSR/hydration,
    # while legacy pages used path suffixes like _P2.htm / _IP2.htm.
    candidates.append(_replace_query_param(base_url, "page", page))
    candidates.append(_replace_query_param(base_url, "p", page))

    if base_url.endswith(".htm"):
        candidates.append(base_url[:-4] + f"_IP{page}.htm")
        candidates.append(base_url[:-4] + f"_P{page}.htm")
    else:
        candidates.append(f"{base_url}?page={page}")

    # Preserve order while removing duplicates.
    return list(dict.fromkeys(candidates))


def get_all_links(
    num_pages: int,
    base_url: str,
    delay_seconds: float = 0.5,
    session: Optional[Any] = None,
) -> List[List[str]]:
    """Collect job links across result pages."""
    all_links: List[List[str]] = []
    seen_links: set[str] = set()
    search_bootstrap: Optional[Dict[str, Any]] = None
    LOGGER.info("Collecting links...")

    for page in range(1, num_pages + 1):
        try:
            if page == 1:
                page_url = _build_page_url(base_url, page)
                page_links, search_bootstrap = _get_search_page_links_and_bootstrap(page_url, session=session)
            else:
                page_url = _build_page_url(base_url, page)
                page_links: List[str] = []
                new_links_count = 0

                if search_bootstrap:
                    try:
                        bff_links = _get_links_from_bff_page(
                            page_number=page,
                            bootstrap=search_bootstrap,
                            session=session,
                        )
                        if bff_links:
                            page_links = bff_links
                            new_links_count = len([link for link in page_links if link not in seen_links])
                            LOGGER.info(
                                "Page %s loaded via BFF pagination (%s links, %s new).",
                                page,
                                len(page_links),
                                new_links_count,
                            )
                    except requests.RequestException as exc:
                        LOGGER.warning("BFF pagination failed for page %s: %s", page, exc)
                    except Exception as exc:  # pragma: no cover - defensive for unstable payloads
                        LOGGER.warning("Unexpected BFF pagination error on page %s: %s", page, exc)

                if not page_links:
                    best_links: List[str] = []
                    best_url: Optional[str] = None
                    best_new_count = -1

                    for candidate_url in _build_page_url_candidates(base_url, page):
                        candidate_links = get_position_links(candidate_url, session=session)
                        candidate_new_count = len([link for link in candidate_links if link not in seen_links])

                        if candidate_new_count > best_new_count:
                            best_new_count = candidate_new_count
                            best_links = candidate_links
                            best_url = candidate_url

                        if candidate_new_count == len(candidate_links) and candidate_links:
                            break

                    page_url = best_url or _build_page_url(base_url, page)
                    page_links = best_links
                    new_links_count = max(best_new_count, 0)
                    LOGGER.info(
                        "Page %s selected URL %s (%s links, %s new).",
                        page,
                        page_url,
                        len(page_links),
                        new_links_count,
                    )

                if page_links and new_links_count == 0:
                    LOGGER.warning(
                        "Page %s returned no new links; stopping pagination to avoid duplicate scraping.",
                        page,
                    )
                    break

            all_links.append(page_links)
            seen_links.update(page_links)
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
