"""Example data pipeline: load raw data and write processed output.

Replace the body of ``process`` with your own data-loading and
transformation logic.  The ``raw_dir`` / ``processed_dir`` paths are
passed from the Makefile so they can be overridden at invocation time.

Usage::

    python src/your_project_name/data/make_dataset.py data/raw data/processed
"""

from __future__ import annotations

import logging
from pathlib import Path

import click

logger = logging.getLogger(__name__)


def process(raw_dir: Path, processed_dir: Path) -> None:
    """Read files from *raw_dir* and write results to *processed_dir*."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    raw_files = [p for p in raw_dir.iterdir() if p.name != ".gitkeep"]

    if not raw_files:
        logger.info("No raw files found in %s — nothing to process.", raw_dir)
        return

    for path in raw_files:
        logger.info("Processing %s", path.name)


@click.command()
@click.argument("raw_dir", type=click.Path(path_type=Path))
@click.argument("processed_dir", type=click.Path(path_type=Path))
def main(raw_dir: Path, processed_dir: Path) -> None:
    """Run the data processing pipeline."""
    logging.basicConfig(level=logging.INFO)
    process(raw_dir, processed_dir)


if __name__ == "__main__":
    main()
