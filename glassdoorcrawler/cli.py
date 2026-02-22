import argparse
import logging

from .scraper import crawl_jobs

DEFAULT_URL = (
    "https://www.glassdoor.com.br/Vaga/"
    "belo-horizonte-desenvolvedor-vagas-SRCH_IL.0,14_IC2514646_KO15,28.htm"
)


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("--pages must be greater than or equal to 1")
    return parsed


def non_negative_float(value: str) -> float:
    parsed = float(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("--delay must be greater than or equal to 0")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Glassdoor job crawler")
    parser.add_argument("--base-url", default=DEFAULT_URL, help="Glassdoor search results URL")
    parser.add_argument(
        "--pages",
        type=positive_int,
        default=1,
        help="Number of result pages to crawl (>= 1)",
    )
    parser.add_argument(
        "--output",
        default="belohorizonte_vagas.xlsx",
        help="Output Excel file path",
    )
    parser.add_argument(
        "--delay",
        type=non_negative_float,
        default=0.5,
        help="Delay between requests in seconds (>= 0)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(levelname)s %(name)s: %(message)s",
    )

    crawl_jobs(
        base_url=args.base_url,
        num_pages=args.pages,
        output_path=args.output,
        delay_seconds=args.delay,
    )


if __name__ == "__main__":
    main()
