#!/usr/bin/env python3
"""Generate project cards and navigation from docs/projects/*/index.md.

The project index.md front matter is the source of truth. The script:
- discovers direct child project folders that contain index.md;
- validates their front matter;
- regenerates the marked project-card and navigation sections;
- removes obsolete "View project" cards outside generated sections when they
  point to project index.md files that no longer exist.
"""
from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote, quote, urlsplit

import yaml

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
PROJECTS_DIR = DOCS / "projects"

HOME_FEATURED_START = "<!-- PROJECT-CARDS:HOME-FEATURED:START -->"
HOME_FEATURED_END = "<!-- PROJECT-CARDS:HOME-FEATURED:END -->"
LIST_FEATURED_START = "<!-- PROJECT-CARDS:LIST-FEATURED:START -->"
LIST_FEATURED_END = "<!-- PROJECT-CARDS:LIST-FEATURED:END -->"
LIST_OTHER_START = "<!-- PROJECT-CARDS:LIST-OTHER:START -->"
LIST_OTHER_END = "<!-- PROJECT-CARDS:LIST-OTHER:END -->"
NAV_START = "# PROJECT-NAV:START"
NAV_END = "# PROJECT-NAV:END"

# Card syntax used by this generator. Used only to remove obsolete cards on the
# homepage/listing page, and only when their "View project" target is missing.
CARD_START_RE = re.compile(r"^\s*-\s+\*\*.*\*\*\s*$")
VIEW_PROJECT_RE = re.compile(r"\[.*?View project.*?\]\(([^)]+)\)", re.IGNORECASE)


@dataclass(frozen=True)
class Project:
    folder: Path
    page: Path
    title: str
    description: str
    date: date | None
    featured: bool
    status: str
    categories: tuple[str, ...]


def read_front_matter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8-sig")
    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        raise ValueError(f"Missing YAML front matter in {path.relative_to(ROOT)}")

    # Accept LF and CRLF files; search for the closing YAML delimiter.
    match = re.search(r"(?m)^---[ \t]*\r?$", text[4:])
    if not match:
        raise ValueError(f"Unclosed YAML front matter in {path.relative_to(ROOT)}")

    raw = text[4 : 4 + match.start()]
    data = yaml.safe_load(raw)
    if not isinstance(data, dict):
        raise ValueError(f"Front matter must be a YAML mapping in {path.relative_to(ROOT)}")
    return data


def parse_date(value: Any, path: Path) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value.strip())
        except ValueError as exc:
            raise ValueError(
                f"Invalid date {value!r} in {path.relative_to(ROOT)}; use YYYY-MM-DD"
            ) from exc
    raise ValueError(f"Invalid date type in {path.relative_to(ROOT)}; use YYYY-MM-DD")


def load_projects() -> list[Project]:
    """Discover project folders automatically; require an index.md in each one."""
    if not PROJECTS_DIR.is_dir():
        raise ValueError(f"Projects directory does not exist: {PROJECTS_DIR}")

    projects: list[Project] = []
    errors: list[str] = []
    seen_titles: set[str] = set()

    for folder in sorted(p for p in PROJECTS_DIR.iterdir() if p.is_dir()):
        page = folder / "index.md"
        if not page.is_file():
            # A folder without index.md is not a project and is intentionally skipped.
            continue
        try:
            meta = read_front_matter(page)
            title = meta.get("title")
            description = meta.get("description")
            featured = meta.get("featured")
            status = meta.get("status", "completed")
            if isinstance(status, str):
                status = status.strip().lower().replace("-", "_").replace(" ", "_")
            categories = meta.get("categories", [])
            project_date = parse_date(meta.get("date"), page)

            if not isinstance(title, str) or not title.strip():
                raise ValueError(f"Missing/non-text title in {page.relative_to(ROOT)}")
            if not isinstance(description, str) or not description.strip():
                raise ValueError(f"Missing/non-text description in {page.relative_to(ROOT)}")
            if status not in ("completed", "in_development"):
                raise ValueError(f"status must be completed or in_development in {page.relative_to(ROOT)}")
            if not isinstance(featured, bool):
                raise ValueError(f"featured must be true/false in {page.relative_to(ROOT)}")
            if not isinstance(categories, list) or any(not isinstance(item, str) for item in categories):
                raise ValueError(
                    f"categories must be a YAML list of strings in {page.relative_to(ROOT)}"
                )

            title_key = title.casefold().strip()
            if title_key in seen_titles:
                raise ValueError(f"Duplicate project title {title!r}")
            seen_titles.add(title_key)

            if project_date is None:
                print(
                    f"WARNING: {page.relative_to(ROOT)} has no date; it will be listed after dated projects.",
                    file=sys.stderr,
                )

            projects.append(
                Project(
                    folder=folder,
                    page=page,
                    title=title.strip(),
                    description=description.strip(),
                    date=project_date,
                    featured=featured,
                    status=status,
                    categories=tuple(item.strip() for item in categories if item.strip()),
                )
            )
        except (ValueError, yaml.YAMLError) as exc:
            errors.append(str(exc))

    if errors:
        raise ValueError("Project metadata validation failed:\n- " + "\n- ".join(errors))
    if not projects:
        raise ValueError(f"No project folders with index.md found in {PROJECTS_DIR}")
    return projects


def sort_projects(projects: list[Project]) -> list[Project]:
    # Newest dated projects first; undated projects after dated ones, alphabetically.
    return sorted(
        projects,
        key=lambda p: (
            p.date is None,
            -p.date.toordinal() if p.date else 0,
            p.title.casefold(),
        ),
    )


def link_from(source_page: Path, target_page: Path) -> str:
    rel = Path(os.path.relpath(target_page, start=source_page.parent)).as_posix()
    return quote(rel, safe="/-._~")


def markdown_safe(value: str) -> str:
    return value.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")


def render_cards(projects: list[Project], source_page: Path) -> str:
    if not projects:
        return "No projects in this section yet."

    lines = ['<div class="grid cards" markdown>', ""]
    for project in projects:
        link = link_from(source_page, project.page)
        title = markdown_safe(project.title)
        description = markdown_safe(project.description)
        lines.extend([f"- **{title}**", "", "    ---", ""])
        if project.status == "in_development":
            lines.extend(["    **Status: In Development**", ""])
        lines.extend([f"    {description}", ""])
        if project.categories:
            topics = " · ".join(markdown_safe(category) for category in project.categories)
            lines.extend([f"    **Topics:** {topics}", ""])
        lines.extend([f"    [:octicons-arrow-right-24: View project]({link})", ""])
    lines.append("</div>")
    return "\n".join(lines)


def render_home_featured(projects: list[Project], source_page: Path) -> str:
    """Featured cards: completed first, development at the end if present."""
    completed = [p for p in projects if p.status != "in_development"]
    development = [p for p in projects if p.status == "in_development"]
    sections = []
    if completed:
        sections.append(render_cards(completed, source_page))
    if development:
        sections.append("### In Development\n\n" + render_cards(development, source_page))
    return "\n\n".join(sections) if sections else "No featured projects yet."


def render_development_group(projects: list[Project], source_page: Path) -> str:
    """Generate a category only when it contains projects."""
    return "## In Development\n\n" + render_cards(projects, source_page) if projects else ""


def render_nav(projects: list[Project]) -> str:
    """Generate TOML navigation: completed projects first, optional dev subgroup.

    A missing development group is omitted altogether, including its label.
    Keep navigation inside the existing PROJECT-NAV marker pair.
    """
    completed = [p for p in projects if p.status != "in_development"]
    development = [p for p in projects if p.status == "in_development"]

    def nav_item(project: Project, indent: str = "    ") -> str:
        relative = project.page.relative_to(DOCS).as_posix()
        title = json.dumps(project.title, ensure_ascii=False)
        target = json.dumps(relative, ensure_ascii=False)
        return f"{indent}{{ {title} = {target} }},"

    lines = [nav_item(p) for p in completed]
    if development:
        lines.append('    { "In Development" = [')
        lines.extend(nav_item(p, indent="      ") for p in development)
        lines.append('    ] },')
    return "\n".join(lines) if lines else "    # No project pages found."


def replace_section(
    text: str, start_marker: str, end_marker: str, body: str, path: Path
) -> str:
    if text.count(start_marker) != 1 or text.count(end_marker) != 1:
        raise ValueError(
            f"Expected exactly one pair of markers {start_marker!r} / {end_marker!r} "
            f"in {path.relative_to(ROOT)}"
        )
    start = text.index(start_marker) + len(start_marker)
    end = text.index(end_marker)
    if end < start:
        raise ValueError(f"Markers are in the wrong order in {path.relative_to(ROOT)}")
    return text[:start] + "\n\n" + body.rstrip() + "\n\n" + text[end:]


def update_page(path: Path, sections: list[tuple[str, str, str]]) -> None:
    text = path.read_text(encoding="utf-8")
    for start_marker, end_marker, body in sections:
        text = replace_section(text, start_marker, end_marker, body, path)
    path.write_text(text, encoding="utf-8", newline="\n")


def remove_obsolete_project_cards(path: Path) -> int:
    """Remove old View project card blocks whose project index.md no longer exists.

    This handles renamed/deleted project folders when old manually-authored cards
    remain outside the generated marker sections. Other links and project content
    are left alone.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    removed = 0
    i = 0
    project_root = PROJECTS_DIR.resolve()

    while i < len(lines):
        match = VIEW_PROJECT_RE.search(lines[i])
        if not match:
            i += 1
            continue

        raw_target = match.group(1).strip()
        parts = urlsplit(raw_target)
        if parts.scheme or parts.netloc or raw_target.startswith(("/", "#")):
            i += 1
            continue
        target_text = unquote(parts.path)
        candidate = (path.parent / target_text).resolve()

        # Only clean links resolving into docs/projects, and only if the target is absent.
        try:
            candidate.relative_to(project_root)
        except ValueError:
            i += 1
            continue
        if candidate.is_file():
            i += 1
            continue

        start = i
        while start >= 0 and not CARD_START_RE.match(lines[start]):
            start -= 1
        if start < 0:
            start = i

        end = i + 1
        while end < len(lines):
            if CARD_START_RE.match(lines[end]) or lines[end].strip() == "</div>":
                break
            end += 1
        # Keep a container's closing tag and the next card intact.
        del lines[start:end]
        removed += 1
        i = start

    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8", newline="\n")
    return removed


def main() -> int:
    try:
        all_projects = sort_projects(load_projects())
        print(f"[generator] Using: {Path(__file__).resolve()}", flush=True)
        for project in all_projects:
            print(f"[generator] status={project.status:15s} featured={str(project.featured):5s} | {project.folder.name}", flush=True)
        completed = [project for project in all_projects if project.status != "in_development"]
        development = [project for project in all_projects if project.status == "in_development"]
        featured_completed = [project for project in completed if project.featured]
        featured_development = [project for project in development if project.featured]
        other_completed = [project for project in completed if not project.featured]

        home = DOCS / "index.md"
        project_listing = PROJECTS_DIR / "index.md"
        update_page(home, [
            (HOME_FEATURED_START, HOME_FEATURED_END,
             render_home_featured(featured_completed + featured_development, home)),
        ])
        other_body = render_cards(other_completed, project_listing) if other_completed else ""
        development_body = render_development_group(development, project_listing)
        if development_body:
            other_body = (other_body + "\n\n" + development_body).strip()
        update_page(project_listing, [
            (LIST_FEATURED_START, LIST_FEATURED_END,
             render_cards(featured_completed, project_listing) if featured_completed else ""),
            (LIST_OTHER_START, LIST_OTHER_END, other_body),
        ])

        # Remove stale manually-authored project cards left outside the markers.
        removed = remove_obsolete_project_cards(home)
        removed += remove_obsolete_project_cards(project_listing)

        config = ROOT / "zensical.toml"
        config_text = config.read_text(encoding="utf-8")
        config_text = replace_section(
            config_text, NAV_START, NAV_END, render_nav(all_projects), config
        )
        config.write_text(config_text, encoding="utf-8", newline="\n")

        # Validate that each generated output has the expected development section.
        generated_home = home.read_text(encoding="utf-8")
        generated_listing = project_listing.read_text(encoding="utf-8")
        generated_nav = config.read_text(encoding="utf-8")
        if development:
            assert "## In Development" in generated_listing, "Missing Projects development section"
            assert '{ "In Development" = [' in generated_nav, "Missing navigation development group"
            if featured_development:
                assert "### In Development" in generated_home, "Missing Home development section"
        else:
            assert "## In Development" not in generated_listing, "Unexpected Projects development section"
            assert '{ "In Development" = [' not in generated_nav, "Unexpected navigation development group"

        print(
            f"Generated project cards: {len(featured_completed) + len(featured_development)} featured, "
            f"{len(other_completed)} other, {len(development)} in development; "
            f"removed {removed} obsolete card(s)."
        )
        return 0
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
