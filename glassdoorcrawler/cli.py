import argparse
import logging

from .scraper import crawl_jobs

DEFAULT_URL = (
    "https://www.glassdoor.com.br/Vaga/"
    "belo-horizonte-desenvolvedor-vagas-SRCH_IL.0,14_IC2514646_KO15,28.htm"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Glassdoor job crawler")
    parser.add_argument("--base-url", default=DEFAULT_URL, help="Glassdoor search results URL")
    parser.add_argument("--pages", type=int, default=1, help="Number of result pages to crawl")
    parser.add_argument(
        "--output",
        default="belohorizonte_vagas.xlsx",
        help="Output Excel file path",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Delay between requests in seconds",
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
