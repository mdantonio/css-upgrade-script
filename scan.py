"""
https://getbootstrap.com/docs/5.0/migration/
"""
import logging
import re
import sys
from pathlib import Path
from typing import List

import cssutils
import typer
from bs4 import BeautifulSoup
from invalid_classes import fontawesome5_to_6, invalid_classes
from loguru import logger as log
from valid_classes import valid_classes

app = typer.Typer()

cssutils.ser.prefs.resolveVariables = True
cssutils_logger = logging.getLogger("CSSUTILS")
cssutils_logger.setLevel(logging.CRITICAL)


INVALID_CLASSES = invalid_classes


def verify_class(class_name: str, ignore_classes: List[str], filename: str) -> bool:

    if class_name in INVALID_CLASSES:
        log.warning(
            "[{}] {} -> {}", filename, class_name, INVALID_CLASSES.get(class_name)
        )
        return False

    if class_name in valid_classes:
        return True

    if class_name in ignore_classes:
        return True

    if class_name.startswith("fa-"):
        return True

    log.info("Unknown class: {}", class_name)
    return False


def scan_file(file: Path, ignore_classes: List[str]) -> None:
    log.debug("Scanning {}", file)

    with open(file) as f:
        html = f.read()

        soup = BeautifulSoup(html, "html.parser")
        for e in soup.find_all(class_=True):
            for c in e["class"]:
                verify_class(c, ignore_classes, file.name)


def parse_css(css_file: Path) -> List[str]:

    log.debug("Parsing {}", css_file)

    rules: List[str] = []

    with open(css_file) as css:

        content = css.read()

        cleaned_content = ""

        # Remove lines starting with // that make cssutils to wronly skip some lines
        for line in content.split("\n"):
            if line.strip().startswith("//"):
                continue

            cleaned_content += f"{line}\n"

        sheet = cssutils.parseString(cleaned_content)
        for rule in sheet:

            if isinstance(rule, cssutils.css.csscomment.CSSComment):
                continue
            if isinstance(rule, cssutils.css.csscharsetrule.CSSCharsetRule):
                continue
            if isinstance(rule, cssutils.css.cssfontfacerule.CSSFontFaceRule):
                continue
            if isinstance(rule, cssutils.css.cssmediarule.CSSMediaRule):
                continue
            if isinstance(rule, cssutils.css.cssunknownrule.CSSUnknownRule):
                continue
            if isinstance(rule, cssutils.css.cssimportrule.CSSImportRule):

                if not rule.href.startswith("./"):
                    continue

                imported_file = css_file.parent.joinpath(rule.href)

                if imported_file.with_suffix(".scss").exists():
                    extra_rules = parse_css(imported_file.with_suffix(".scss"))
                    rules = rules + extra_rules
                elif imported_file.with_suffix(".css").exists():
                    extra_rules = parse_css(imported_file.with_suffix(".css"))
                    rules = rules + extra_rules

                else:
                    log.warning("Unknown sub-css {}", imported_file)

                continue

            selectors = re.split(r"\s|,", rule.selectorText)

            for s in selectors:

                if "." not in s:
                    continue

                # strip the prefix to return the from the last occurrence of dot
                # .xyz => xzy
                # span.xyz => xyz
                # .a.b.c.xzy => xyz
                s = s[1 + s.rfind(".") :]

                # Remove ::after and ::before
                if "::" in s:
                    s = s[0 : s.find("::")]
                # Remove :hover and :focus
                if ":" in s:
                    s = s[0 : s.find(":")]
                rules.append(s)
    return rules


@app.command()
def scan(
    folder: Path = typer.Argument(..., help="Path of the folder to be scanned"),
    recursive: bool = typer.Option(
        False,
        "--recursive",
        help="Recursively scan subfolders",
        show_default=False,
    ),
    ignore_classes: List[str] = typer.Option(
        None, "--ignore", "-i", help="Ignore the specified css classes"
    ),
    fontawesome: bool = typer.Option(
        False,
        "--fontawesome",
        help="Include FontAwesome v5 to v6 upgraded classes",
        show_default=False,
    ),
) -> None:

    if not folder.exists():
        log.critical("Path {} does not exists", folder)
        sys.exit(1)

    if fontawesome:
        INVALID_CLASSES.update(fontawesome5_to_6)

    if not ignore_classes:
        ignore_classes = []
    else:
        ignore_classes = list(ignore_classes)

    if recursive:
        css_files = list(folder.rglob("*.scss"))
        css_files = css_files + list(folder.rglob("*.css"))
    else:
        css_files = list(folder.glob("*.scss"))
        css_files = css_files + list(folder.glob("*.css"))

    for f in css_files:
        ignore_classes = ignore_classes + parse_css(f)

    if recursive:
        files = folder.rglob("*.html")
    else:
        files = folder.glob("*.html")

    for f in files:
        scan_file(f, ignore_classes)


if __name__ == "__main__":
    app()
