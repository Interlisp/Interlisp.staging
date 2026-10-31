#!/usr/bin/env python3
"""Render the staging root pages from templates and a list of previews."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import pathlib
import re
import shutil
import sys
from collections.abc import Iterable

BASE_PATH = "/Interlisp.staging/"
PLACEHOLDER_BASE = "{{BASE_PATH}}"
PLACEHOLDER_PREVIEWS = "<!-- PREVIEWS -->"
PLACEHOLDER_UPDATED = "<!-- UPDATED -->"
STATIC_FILES = ("root.css", "robots.txt", ".nojekyll")


def parse_preview_lines(lines: Iterable[str]) -> list[int]:
    """Return validated, deduplicated preview numbers, newest first."""
    numbers: set[int] = set()
    for line in lines:
        value = line.strip()
        if not value:
            continue
        if not re.fullmatch(r"[0-9]+", value):
            raise ValueError(f"invalid preview number: {value!r}")
        numbers.add(int(value))
    return sorted(numbers, reverse=True)


def parse_previews(path: pathlib.Path) -> list[int]:
    return parse_preview_lines(path.read_text(encoding="utf-8").splitlines())


def render_previews(previews: list[int]) -> str:
    if not previews:
        return '      <li class="muted">No previews are currently deployed.</li>'
    return "\n".join(
        f'      <li><a href="pr-{number}/">Pull request #{number}</a></li>'
        for number in previews
    )


def render_template(template: str, previews: list[int], updated: str) -> str:
    rendered = template.replace(PLACEHOLDER_BASE, BASE_PATH)
    rendered = rendered.replace(PLACEHOLDER_PREVIEWS, render_previews(previews))
    rendered = rendered.replace(PLACEHOLDER_UPDATED, html.escape(updated))
    for placeholder in (PLACEHOLDER_BASE, PLACEHOLDER_PREVIEWS, PLACEHOLDER_UPDATED):
        if placeholder in rendered:
            raise ValueError(f"unrendered placeholder: {placeholder}")
    return rendered


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--templates-dir",
        type=pathlib.Path,
        default=pathlib.Path(".github/pages"),
    )
    parser.add_argument("--previews-file", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args(argv)

    previews = parse_previews(args.previews_file)
    updated = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    args.output.mkdir(parents=True, exist_ok=True)
    for template_name, output_name in (
        ("index.template.html", "index.html"),
        ("404.template.html", "404.html"),
    ):
        template = (args.templates_dir / template_name).read_text(encoding="utf-8")
        (args.output / output_name).write_text(
            render_template(template, previews, updated),
            encoding="utf-8",
        )
    for name in STATIC_FILES:
        shutil.copyfile(args.templates_dir / name, args.output / name)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
