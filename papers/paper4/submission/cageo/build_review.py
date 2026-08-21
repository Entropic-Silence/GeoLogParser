#!/usr/bin/env python3
"""Build the Paper 4 Computers & Geosciences internal review manuscript.

The scientific Markdown remains the source of truth. This script only
formats a review artifact and asserts that frozen headline values are still
present before emitting the LaTeX source.
"""

from __future__ import annotations

import hashlib
import re
import sys
import unicodedata
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
PAPER = REPO / "papers" / "paper4"


TITLE = (
    "Trustworthy Borehole Database Ingestion from VLM Proposals: "
    "Provenance and Spatial Support"
)

FROZEN_STRINGS = [
    "450 reports",
    "8,268 intervals",
    "0.896–0.932",
    "0.577",
    "0.993",
    "444/447",
    "0.244",
    "4/100",
    "0.1387",
    "0.1213",
    "0.0821",
    "0.0326",
    "0.0754",
    "0.636",
    "partially reconstructable",
    "contamination",
    "IDW",
]


def normalize_unicode(text: str) -> str:
    replacements = {
        "–": "--",
        "—": "---",
        "‑": "-",
        "“": "``",
        "”": "''",
        "’": "'",
        "×": r"\ensuremath{\times}",
        "≤": r"\ensuremath{\leq}",
        "≥": r"\ensuremath{\geq}",
        "±": r"\ensuremath{\pm}",
        "≈": r"\ensuremath{\approx}",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def manuscript_highlights(source: str) -> list[str]:
    block = source.split("## Highlights", 1)[1].split("## 1.", 1)[0]
    highlights = [
        line[2:].strip()
        for line in block.splitlines()
        if line.startswith("- ")
    ]
    if not 3 <= len(highlights) <= 5:
        raise ValueError(f"Expected 3–5 manuscript highlights, found {len(highlights)}")
    return highlights


def extract_latex_abstract(pandoc_body: str) -> str:
    match = re.search(
        r"\\(?:sub)*section\{Abstract\}(?:\\label\{abstract\})?\s*"
        r"(.*?)\s*(?=\\textbf\{Keywords:\})",
        pandoc_body,
        flags=re.S,
    )
    if not match:
        raise ValueError("Pandoc body does not contain the manuscript abstract")
    return match.group(1).strip()


def bind_figure_labels(body: str) -> str:
    labels = {
        1: "fig:framework",
        2: "fig:capability",
        3: "fig:assurance",
        4: "fig:spatial",
    }
    for number, label in labels.items():
        pattern = rf"\\caption\{{Figure {number}\. ([^\n]+)\}}"
        matches = list(re.finditer(pattern, body))
        if len(matches) != 1:
            raise ValueError(
                f"Expected one source caption for Figure {number}, found {len(matches)}"
            )
        caption = matches[0].group(1)
        body = re.sub(
            pattern,
            lambda _: rf"\caption{{{caption}}}\label{{{label}}}",
            body,
            count=1,
        )
    return body


def replace_sections(body: str) -> str:
    section_map = {
        r"\\subsection\{1\. Problem, hypothesis, and research questions\}.*": r"\\section{Introduction}",
        r"\\subsection\{2\. Related work and positioning\}.*": r"\\section{Related Work}",
        r"\\subsection\{3\. Evidence, data, and task definition\}.*": r"\\section{Data, Evidence Tiers, and Task Definition}",
        r"\\subsection\{4\. Methods: provenance-grounded selective assurance\}.*": r"\\section{Provenance-Grounded Selective Assurance}",
        r"\\subsection\{5\. Experimental protocol and reproducibility\}.*": r"\\section{Experimental Design and Reproducibility}",
        r"\\subsection\{6\. Results\}.*": r"\\section{Results}",
        r"\\subsection\{7\. Discussion\}.*": r"\\section{Discussion}",
        r"\\subsection\{8\. Limitations and threats to validity\}.*": r"\\section{Limitations and Threats to Validity}",
        r"\\subsection\{9\. Conclusions\}.*": r"\\section{Conclusions}",
        r"\\subsection\{Computer Code Availability\}.*": r"\\section*{Computer Code Availability}",
        r"\\subsection\{Data Availability\}.*": r"\\section*{Data Availability}",
        r"\\subsection\{Declarations\}.*": r"\\section*{Declarations}",
        r"\\subsection\{References\}.*": r"",
    }
    for pattern, replacement in section_map.items():
        body = re.sub(pattern, replacement, body)
    body = re.sub(
        r"\\subsubsection\{\d+\.\d+\s+([^}]*)\}.*",
        r"\\subsection{\1}",
        body,
    )
    return body


def repair_body(body: str) -> str:
    body = normalize_unicode(body)
    # Pandoc 2.9 wraps every heading in a ``hypertarget`` block.  The section
    # relabeling below intentionally replaces the inner heading line; remove
    # the now-unpaired wrapper so Ubuntu's packaged Pandoc and the pinned
    # publication toolchain produce valid LaTeX alike.
    body = re.sub(r"\\hypertarget\{[^{}]+\}\{%\n", "", body)
    body = replace_sections(body)
    body = body.replace(
        r"Fixed ACCEPT/NEEDS\_REVIEW",
        r"\makecell[l]{Fixed\\ACCEPT/\\NEEDS\_\\REVIEW}",
    )
    body = body.replace(
        "  >{\\raggedright\\arraybackslash}p{(\\linewidth - 14\\tabcolsep) * \\real{0.1250}}\n"
        "  >{\\raggedright\\arraybackslash}p{(\\linewidth - 14\\tabcolsep) * \\real{0.1250}}",
        "  >{\\raggedright\\arraybackslash}p{(\\linewidth - 14\\tabcolsep) * \\real{0.1220}}\n"
        "  >{\\raggedright\\arraybackslash}p{(\\linewidth - 14\\tabcolsep) * \\real{0.1280}}",
        1,
    )
    body = re.sub(r"\\pandocbounded\{(\\includegraphics\[.*?\]\{.*?\})\}", r"\1", body)
    body = body.replace("figures/F1_trustworthy_framework.png", "figures/Figure_1.pdf")
    body = body.replace("figures/F2_vlm_source_shift.png", "figures/Figure_2.pdf")
    body = body.replace("figures/F3_assurance_frontier.png", "figures/Figure_3.pdf")
    body = body.replace("figures/F4_spatial_support_consequence.png", "figures/Figure_4.pdf")
    body = body.replace(
        r"\includegraphics[keepaspectratio,alt=",
        r"\includegraphics[width=0.94\textwidth,keepaspectratio,alt=",
    )
    body = re.sub(r"\\texttt\{([0-9a-f]{40,})\}", r"\\path{\1}", body)
    body = re.sub(r"\\texttt\{([^{}]{45,})\}", r"\\path{\1}", body)
    body = body.replace(r"\\textless{}", "$<$")
    body = body.replace(r"\\textgreater{}", "$>$")
    zero_event_math = (
        r"For \(n\) accepted documents and zero observed worsened documents, "
        r"the one-sided 95\% upper bound is \(1 - 0.05^{1/n}\);"
    )
    for zero_event_literal in (
        r"For (n) accepted documents and zero observed worsened documents, "
        r"the one-sided 95\% upper bound is (1 - 0.05\^{}\{1/n\});",
        r"For (n) accepted documents and zero observed worsened documents, "
        r"the one-sided 95\% upper bound is (1-0.05\^{}\{1/n\});",
    ):
        body = body.replace(zero_event_literal, zero_event_math)
    body = body.replace(r"(10\^{}\{-6\})", r"\(10^{-6}\)")

    body = body.replace(
        "The direct-VLM baseline, positioned parser, sequence decoder, risk policy, and spatial diagnostics are deterministic given the frozen page renders, candidate pools, configuration files, and seeds.",
        "The evaluation protocol and deterministic post-processing components were frozen. The VLM used fixed decoding settings, while bitwise deterministic execution is not claimed.",
    )
    body = body.replace(
        "Source PDFs and transformed inputs are distributed under the project release policy; provenance and final rights checks remain explicit in the ledger.",
        "The article package releases structured/reanalysis assets, manifests, hashes, source URLs, and recomputation materials. The separately versioned data-v002 companion contains the selected source files and structured datasets that passed the author's item-level rights, attribution, linkage, privacy, sensitive-location, and embedded-content review. Model weights and private credentials are not redistributed.",
    )
    body = re.sub(r"Shared bibliography:.*?(?:\n|$)", "", body)
    body = re.sub(r"\\section\*\\?\{References\}(?:\\label\{references\})?", "", body)
    return body


def tables_tex() -> tuple[str, str, str]:
    reliability = r"""
\begingroup
\singlespacing
\footnotesize
\setlength{\tabcolsep}{2pt}
\begin{longtable}{@{}>{\raggedright\arraybackslash}p{0.17\textwidth}>{\raggedright\arraybackslash}p{0.17\textwidth}>{\raggedright\arraybackslash}p{0.23\textwidth}rrr@{}}
\caption{Boundary-pair interval F1 across cohorts, readers, and source-shift panels. These are the results shown in Fig.~2; evidence tiers are declared separately and are not pooled.}\label{tab:reliability}\\
\toprule
Panel & Reader/interface & Evidence tier & Documents & \makecell{Reference\\intervals} & \makecell{Boundary-pair\\interval F1} \\
\midrule
\endfirsthead
\caption[]{Boundary-pair interval F1 across cohorts, readers, and source-shift panels (continued)}\\
\toprule
Panel & Reader/interface & Evidence tier & Documents & \makecell{Reference\\intervals} & \makecell{Boundary-pair\\interval F1} \\
\midrule
\endhead
\midrule
\multicolumn{6}{r}{Continued on next page}\\
\endfoot
\bottomrule
\endlastfoot
California v001 & Qwen direct & Published manual-transcription Gold & 50 & 697 & 0.932 \\
California v001 & RapidOCR positioned & Published manual-transcription Gold & 50 & 697 & 0.390 \\
California v002 & Qwen direct & Published manual-transcription Gold & 100 & 1,770 & 0.896 \\
California v002 & RapidOCR positioned & Published manual-transcription Gold & 100 & 1,770 & 0.450 \\
California v003 & Qwen direct & Published manual-transcription Gold & 100 & 1,788 & 0.918 \\
California v003 & RapidOCR positioned & Published manual-transcription Gold & 100 & 1,788 & 0.383 \\
California v004 & Qwen direct & Published manual-transcription Gold & 100 & 1,944 & 0.917 \\
California v004 & RapidOCR positioned & Published manual-transcription Gold & 100 & 1,944 & 0.428 \\
California v005 & Qwen direct & Published manual-transcription Gold & 100 & 2,069 & 0.903 \\
California v005 & RapidOCR positioned & Published manual-transcription Gold & 100 & 2,069 & 0.389 \\
Swissgeol held-out & Qwen direct & Source-agreement reference & 35 & 80 & 0.577 \\
Swissgeol held-out & RapidOCR positioned & Source-agreement reference & 35 & 80 & 0.679 \\
Swissgeol held-out & Tesseract positioned & Source-agreement reference & 35 & 80 & 0.857 \\
BGS Offshore & RapidOCR positioned & Source-agreement reference & 26 & 341 & 0.038 \\
BGS Offshore & Tesseract positioned & Source-agreement reference & 26 & 341 & 0.041 \\
Raft River & RapidOCR positioned & Source-agreement reference & 2 & 62 & 1.000 \\
\end{longtable}
\endgroup
"""
    assurance = r"""
\begingroup
\singlespacing
\footnotesize
\setlength{\tabcolsep}{1.5pt}
\begin{longtable}{@{}>{\raggedright\arraybackslash}p{0.13\textwidth}>{\centering\arraybackslash}p{0.09\textwidth}>{\centering\arraybackslash}p{0.11\textwidth}>{\centering\arraybackslash}p{0.11\textwidth}>{\centering\arraybackslash}p{0.09\textwidth}>{\centering\arraybackslash}p{0.07\textwidth}>{\raggedright\arraybackslash}p{0.17\textwidth}>{\centering\arraybackslash}p{0.06\textwidth}@{}}
\caption{Independent evidence and selective assurance. Raw proposal precision, endpoint-field anchor coverage, both-endpoint interval coverage, and accepted coverage use distinct quantities and denominators.}\label{tab:assurance}\\
\toprule
Cohort & \makecell{Raw\\proposal\\precision} & \makecell{Endpoint-\\field anchor\\coverage} & \makecell{Both-\\endpoint anchor\\coverage} & \makecell{Accepted\\coverage} & \makecell{Accepted\\interval\\count} & \makecell[l]{Selective precision\\(95\% CI)} & \makecell{Error\\docs} \\
\midrule
\endfirsthead
\caption[]{Independent evidence and selective assurance (continued)}\\
\toprule
Cohort & \makecell{Raw\\proposal\\precision} & \makecell{Endpoint-\\field anchor\\coverage} & \makecell{Both-\\endpoint anchor\\coverage} & \makecell{Accepted\\coverage} & \makecell{Accepted\\interval\\count} & \makecell[l]{Selective precision\\(95\% CI)} & \makecell{Error\\docs} \\
\midrule
\endhead
\bottomrule
\endfoot
California v001 development & 0.908 & 0.817 & 0.731 & 0.236 & 174 & 1.000 [1.000, 1.000] & 0 \\
California v002 validation & 0.854 & 0.849 & 0.792 & 0.287 & 561 & 0.979 [0.951, 0.997] & 5 \\
California v003 held-out & 0.907 & 0.845 & 0.791 & 0.244 & 447 & 0.993 [0.984, 1.000] & 3 \\
\end{longtable}
\endgroup
"""
    spatial = r"""
\begingroup
\singlespacing
\footnotesize
\begin{longtable}{@{}lrrr@{}}
\caption{Risk, coverage, and downstream support diagnostics.}\label{tab:spatial}\\
\toprule
Analysis & Raw & Reread & Risk-aware \\
\midrule
\endfirsthead
\caption[]{Risk, coverage, and downstream support diagnostics (continued)}\\
\toprule
Analysis & Raw & Reread & Risk-aware \\
\midrule
\endhead
\bottomrule
\endfoot
Full-support volume discrepancy & 0.1387 & 0.1213 & 0.0821 \\
Matched-subset volume discrepancy & 0.0326 & 0.0754 & 0.0754 \\
First-boundary hull-area ratio & 1.000 & 1.000 & 0.636 \\
Default LOO MAE (m) & 49.84 & 46.62 & 47.05 \\
\end{longtable}
\endgroup
"""
    return reliability, assurance, spatial


def tables_markdown() -> tuple[str, str, str]:
    reliability = r"""
**Table 3.** Boundary-pair interval F1 across cohorts, readers, and source-shift panels. These are the results shown in Figure 2; evidence tiers are declared separately and are not pooled.

| Panel | Reader/interface | Evidence tier | Documents | Reference intervals | Boundary-pair interval F1 |
|---|---|---|---:|---:|---:|
| California v001 | Qwen direct | Published manual-transcription Gold | 50 | 697 | 0.932 |
| California v001 | RapidOCR positioned | Published manual-transcription Gold | 50 | 697 | 0.390 |
| California v002 | Qwen direct | Published manual-transcription Gold | 100 | 1,770 | 0.896 |
| California v002 | RapidOCR positioned | Published manual-transcription Gold | 100 | 1,770 | 0.450 |
| California v003 | Qwen direct | Published manual-transcription Gold | 100 | 1,788 | 0.918 |
| California v003 | RapidOCR positioned | Published manual-transcription Gold | 100 | 1,788 | 0.383 |
| California v004 | Qwen direct | Published manual-transcription Gold | 100 | 1,944 | 0.917 |
| California v004 | RapidOCR positioned | Published manual-transcription Gold | 100 | 1,944 | 0.428 |
| California v005 | Qwen direct | Published manual-transcription Gold | 100 | 2,069 | 0.903 |
| California v005 | RapidOCR positioned | Published manual-transcription Gold | 100 | 2,069 | 0.389 |
| Swissgeol held-out | Qwen direct | Source-agreement reference | 35 | 80 | 0.577 |
| Swissgeol held-out | RapidOCR positioned | Source-agreement reference | 35 | 80 | 0.679 |
| Swissgeol held-out | Tesseract positioned | Source-agreement reference | 35 | 80 | 0.857 |
| BGS Offshore | RapidOCR positioned | Source-agreement reference | 26 | 341 | 0.038 |
| BGS Offshore | Tesseract positioned | Source-agreement reference | 26 | 341 | 0.041 |
| Raft River | RapidOCR positioned | Source-agreement reference | 2 | 62 | 1.000 |
"""
    assurance = r"""
**Table 4.** Independent evidence and selective assurance. Raw proposal precision, endpoint-field anchor coverage, both-endpoint interval coverage, and accepted coverage use distinct quantities and denominators.

| Cohort | Raw proposal precision | Endpoint-field anchor coverage | Both-endpoint anchor coverage | Accepted coverage | Accepted intervals (n) | Selective precision (95% CI) | Error docs |
|---|---:|---:|---:|---:|---:|---|---:|
| California v001 development | 0.908 | 0.817 | 0.731 | 0.236 | 174 | 1.000 [1.000, 1.000] | 0 |
| California v002 validation | 0.854 | 0.849 | 0.792 | 0.287 | 561 | 0.979 [0.951, 0.997] | 5 |
| California v003 held-out | 0.907 | 0.845 | 0.791 | 0.244 | 447 | 0.993 [0.984, 1.000] | 3 |
"""
    spatial = r"""
**Table 5.** Risk, coverage, and downstream support diagnostics.

| Analysis | Raw | Reread | Risk-aware |
|---|---:|---:|---:|
| Full-support volume discrepancy | 0.1387 | 0.1213 | 0.0821 |
| Matched-subset volume discrepancy | 0.0326 | 0.0754 | 0.0754 |
| First-boundary hull-area ratio | 1.000 | 1.000 | 0.636 |
| Default LOO MAE (m) | 49.84 | 46.62 | 47.05 |
"""
    return reliability, assurance, spatial


def insert_after_latex_figure(body: str, filename: str, content: str) -> str:
    marker = "{" + filename + "}"
    start = body.find(marker)
    if start < 0:
        raise ValueError(f"LaTeX figure marker not found: {filename}")
    end_marker = r"\end{figure}"
    end = body.find(end_marker, start)
    if end < 0:
        raise ValueError(f"LaTeX figure end not found: {filename}")
    end += len(end_marker)
    return body[:end] + "\n\\FloatBarrier\n" + content + body[end:]


def add_longtable_continuation_caption(body: str, label: str, caption: str) -> str:
    """Add an unlisted continuation caption to a Pandoc-generated longtable."""
    table_marker = f"\\label{{{label}}}\\tabularnewline"
    table_start = body.find(table_marker)
    if table_start < 0:
        # Pandoc 2.9 serializes a table identifier inside the caption as
        # ``\{\#tab:name\}`` instead of emitting a standalone ``\label``.
        # Locate the nearest caption start so the same continuation-caption
        # logic remains valid on the Ubuntu package toolchain.
        token = r"\#" + label
        token_pos = body.find(token)
        if token_pos >= 0:
            caption_start = body.rfind(r"\caption{", 0, token_pos)
            caption_end = body.find(r"\tabularnewline", token_pos)
            if caption_start >= 0 and caption_end >= 0:
                caption_text = body[caption_start:caption_end]
                caption_text = caption_text.replace(r"\{\#" + label + r"\}", "")
                caption_text += f"\\label{{{label}}}"
                body = body[:caption_start] + caption_text + body[caption_end:]
                table_marker = f"\\label{{{label}}}\\tabularnewline"
                table_start = body.find(table_marker)
    if table_start < 0:
        raise ValueError(f"Longtable label not found: {label}")
    first_head_end = body.find("\\endfirsthead", table_start)
    if first_head_end < 0:
        raise ValueError(f"Longtable first-head boundary not found: {label}")
    insert_at = first_head_end + len("\\endfirsthead")
    continued = f"\n\\caption[]{{{caption} (continued)}}\\tabularnewline"
    return body[:insert_at] + continued + body[insert_at:]


def insert_after_markdown_figure(text: str, filename: str, content: str) -> str:
    marker = "](" + filename + ")"
    start = text.find(marker)
    if start < 0:
        raise ValueError(f"Markdown figure marker not found: {filename}")
    end = text.find("\n", start)
    if end < 0:
        end = len(text)
    return text[:end] + "\n" + content + text[end:]


def _bib_field(entry: str, field: str) -> str:
    """Extract one BibTeX field while respecting nested braces."""
    match = re.search(rf"(?m)^\s*{re.escape(field)}\s*=\s*", entry)
    if not match:
        return ""
    i = match.end()
    while i < len(entry) and entry[i].isspace():
        i += 1
    if i >= len(entry):
        return ""
    if entry[i] in '{"':
        opener = entry[i]
        closer = '}' if opener == '{' else '"'
        depth = 0
        j = i
        while j < len(entry):
            ch = entry[j]
            if opener == '{' and ch == '{':
                depth += 1
            elif opener == '{' and ch == '}':
                depth -= 1
                if depth == 0:
                    return entry[i + 1:j]
            elif opener == '"' and ch == closer and (j == i or entry[j - 1] != '\\'):
                return entry[i + 1:j]
            j += 1
        return entry[i + 1:]
    return entry[i:].split(',', 1)[0].strip()


def _clean_bib(value: str) -> str:
    value = value.replace('\\&', '&').replace('\\_', '_').replace('~', ' ')
    value = value.replace('---', ' - ').replace('--', '-')
    value = re.sub(
        r"\{\\'\{?([A-Za-z])\}?\}",
        lambda match: unicodedata.normalize("NFC", match.group(1) + "\u0301"),
        value,
    )
    value = re.sub(r"\\[aeiouAEIOU]\\?", "", value)
    value = re.sub(r"\\[A-Za-z]+", "", value)
    value = value.replace('{', '').replace('}', '')
    return re.sub(r"\s+", " ", value).strip()


def markdown_references(bibliography: str) -> str:
    entries = [entry.strip() for entry in re.split(r"(?=^@)", bibliography, flags=re.M) if entry.strip()]
    lines = ["## References", "", "The reference records below are the same cited entries used to build the PDF bibliography.", ""]
    for entry in entries:
        key_match = re.match(r"@\w+\{([^,]+),", entry)
        if not key_match:
            continue
        key = key_match.group(1)
        authors = _clean_bib(_bib_field(entry, "author")).replace(" and ", "; ")
        year = _clean_bib(_bib_field(entry, "year"))
        title = _clean_bib(_bib_field(entry, "title"))
        venue = _clean_bib(_bib_field(entry, "journal") or _bib_field(entry, "booktitle") or _bib_field(entry, "institution") or _bib_field(entry, "publisher"))
        details = [f"{authors} ({year}). {title}."]
        if venue:
            details.append(venue)
        volume = _clean_bib(_bib_field(entry, "volume"))
        number = _clean_bib(_bib_field(entry, "number"))
        pages = _clean_bib(_bib_field(entry, "pages"))
        if volume:
            details.append(f"{volume}{f'({number})' if number else ''}")
        if pages:
            details.append(f"pp. {pages}")
        doi = _clean_bib(_bib_field(entry, "doi"))
        url = _clean_bib(_bib_field(entry, "url"))
        if doi:
            details.append(f"https://doi.org/{doi}")
        elif url:
            details.append(url)
        lines.append(f"- **{key}.** " + " ".join(details))
    return "\n".join(lines) + "\n"


def extract_bibliography(source: str, cited_keys: list[str]) -> str:
    entries = re.split(r"(?=^@)", source, flags=re.M)
    by_key: dict[str, str] = {}
    for entry in entries:
        match = re.match(r"@\w+\{([^,]+),", entry.strip())
        if match:
            by_key[match.group(1)] = entry.strip() + "\n"
    missing = [key for key in cited_keys if key not in by_key]
    if missing:
        raise ValueError(f"Missing bibliography keys: {missing}")
    return "\n".join(by_key[key] for key in cited_keys)


def word_count(source: str) -> tuple[int, int, int, int]:
    abstract = source.split("## Abstract", 1)[1].split("**Keywords:**", 1)[0]
    body = source.split("## 1. Problem, hypothesis, and research questions", 1)[1].split("## References", 1)[0]
    body_no_captions = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", body)
    body_no_captions = re.sub(
        r"(?m)^(?:\*\*Table \d+\.\*\*|Table:).*$",
        "",
        body_no_captions,
    )
    body_lines = [
        line
        for line in body_no_captions.splitlines()
        if not line.lstrip().startswith("|")
    ]
    body_no_tables = "\n".join(body_lines)
    keywords = source.split("**Keywords:**", 1)[1].split("\n", 1)[0]
    highlights = "\n".join(line[2:] for line in source.split("## Highlights", 1)[1].split("## 1.", 1)[0].splitlines() if line.startswith("- "))
    count = lambda text: len(re.findall(r"\b[\w'-]+\b", text))
    return (
        count(abstract),
        count(body_no_tables),
        count(body_no_captions),
        count(keywords) + count(highlights),
    )


def main() -> None:
    final_mode = "--final" in sys.argv[1:]
    body_path = HERE / "body_pandoc.tex"
    positional = [arg for arg in sys.argv[1:] if arg != "--final"]
    if positional:
        body_path = Path(positional[0]).resolve()
    source_path = PAPER / "manuscript.md"
    source = source_path.read_text(encoding="utf-8")
    source_sha256 = hashlib.sha256(source_path.read_bytes()).hexdigest()
    highlights = manuscript_highlights(source)
    for frozen in FROZEN_STRINGS:
        if frozen not in source:
            raise ValueError(f"Frozen source check failed: {frozen}")
    pandoc_body = body_path.read_text(encoding="utf-8")
    abstract_tex = extract_latex_abstract(pandoc_body)
    start = pandoc_body.find(r"\subsection{1. Problem, hypothesis, and research questions}")
    if start < 0:
        raise ValueError("Pandoc body does not contain the expected Introduction heading")
    body = bind_figure_labels(repair_body(pandoc_body[start:]))

    # Citation keys occur as Markdown citation tokens; do not treat the
    # author's email address (for example, ``@gmail``) as a bibliography key.
    cited_keys = sorted(
        set(re.findall(r"(?<![A-Za-z0-9._%+-])@([A-Za-z0-9_:-]+)", source))
    )
    bibliography = extract_bibliography((PAPER.parent / "references.bib").read_text(encoding="utf-8"), cited_keys)
    (HERE / "references_cageo.bib").write_text(bibliography, encoding="utf-8", newline="\n")

    abstract_words, main_words, body_words, excluded_words = word_count(source)
    (HERE / "word_count.txt").write_text(
        "Paper 4 C&G manuscript word count\n"
        f"Abstract: {abstract_words}\n"
        f"Main-text approximate C&G words (tables and captions excluded): {main_words}\n"
        f"Article body including inline Markdown table text (captions excluded): {body_words}\n"
        "References excluded: yes\n"
        "Captions excluded: yes\n"
        "Keywords/highlights excluded: yes\n"
        "Note: counts are source-Markdown estimates; final submission-system count must be run on manuscript.tex.\n",
        encoding="utf-8",
        newline="\n",
    )

    for index, highlight in enumerate(highlights, 1):
        print(f"highlight_{index}_characters={len(highlight)}")
        if len(highlight) > 85:
            raise ValueError(f"Highlight {index} exceeds 85 characters")
    (HERE / "highlights.txt").write_text(
        "\n".join(highlights) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    if final_mode:
        preamble_note = "%% FINAL MANUSCRIPT SOURCE"
        footer_definition = r"""\ExplSyntaxOn
\cs_gset:Npn \__first_footerline: { }
\ExplSyntaxOff"""
        shorttitle = TITLE
        shortauthors = "Du"
        review_box = ""
    else:
        preamble_note = "%% INTERNAL ACADEMIC REVIEW DRAFT"
        footer_definition = r"""\ExplSyntaxOn
\cs_gset:Npn \__first_footerline:
  { \group_begin: \small \sffamily \textnormal{Internal~academic~review~draft~--~not~for~submission} \group_end: }
\ExplSyntaxOff"""
        shorttitle = "Internal review draft"
        shortauthors = "Du"
        review_box = r"""\begin{center}
\fbox{\parbox{0.84\textwidth}{\centering\small\textbf{DRAFT FOR INTERNAL ACADEMIC REVIEW}\\NOT FOR SUBMISSION\\[2pt]Scientific content frozen; metadata and declarations populated for review.}}
\end{center}
\vspace{1em}"""

    # C&G asks for line numbers in the editable submission.  Keep them in the
    # final source, but define the digest as an unbreakable box below so
    # lineno cannot insert a line number between hexadecimal characters.
    line_number_package = r"\usepackage{lineno}"
    line_numbers = r"\linenumbers"

    header = rf"""{preamble_note}
%% Scientific content is retained from papers/paper4/manuscript.md.
%% Canonical Markdown SHA-256: {source_sha256}
\documentclass[a4paper,fleqn]{{cas-sc}}
\usepackage[authoryear]{{natbib}}
\usepackage{{graphicx}}
\usepackage{{float}}
\usepackage{{setspace}}
{line_number_package}
\usepackage{{longtable}}
\usepackage{{booktabs}}
\usepackage{{array}}
\usepackage{{tabularx}}
\usepackage{{makecell}}
\usepackage{{calc}}
\usepackage{{adjustbox}}
\usepackage{{seqsplit}}
\usepackage{{xcolor}}
\usepackage{{enumitem}}
\usepackage{{microtype}}
\usepackage{{placeins}}
\hypersetup{{
  hidelinks,
  hypertexnames=false,
  pdftitle={{{TITLE}}},
  pdfauthor={{Yifan Du}},
  pdfsubject={{Provenance-grounded selective assurance for borehole database ingestion}},
  pdfkeywords={{borehole logs, vision-language models, provenance, selective prediction, spatial support, geoscience computing}}
}}
\newcommand{{\pandocbounded}}[1]{{#1}}
\newcommand{{\tightlist}}{{}}
\newcommand{{\real}}[1]{{#1}}
\newcommand{{\hash}}[1]{{\mbox{{\texttt{{#1}}}}}}
\newcolumntype{{Y}}{{>{{\raggedright\arraybackslash}}X}}
\graphicspath{{{{../../}}}}
\setlength{{\emergencystretch}}{{3em}}
{line_numbers}
\begin{{document}}
{footer_definition}
\let\WriteBookmarks\relax
\shorttitle{{{shorttitle}}}
\shortauthors{{{shortauthors}}}
\title[mode=title]{{{TITLE}}}
\author[1]{{Yifan Du}}[auid=000,orcid=0009-0008-7740-5408]
\cormark[1]
\ead{{duyifan619916@gmail.com}}
\credit{{Conceptualization; Data curation; Formal analysis; Investigation; Methodology; Project administration; Resources; Software; Validation; Visualization; Writing -- original draft; Writing -- review and editing}}
\address[1]{{North China University of Water Resources and Electric Power, Zhengzhou, Henan 450046, China}}
\begingroup
\ExplSyntaxOn
\cs_set:Npn \msg_term:n #1 {{}}
\ExplSyntaxOff
\cortext[cor1]{{Corresponding author.}}
\endgroup
\begin{{abstract}}
{abstract_tex}
\end{{abstract}}
"""
    highlights_block = "\n".join(
        "\\item " + normalize_unicode(highlight).replace("%", "\\%")
        for highlight in highlights
    )
    header += r"""
\begin{keywords}
borehole logs \sep vision-language models \sep provenance \sep selective prediction \sep spatial support \sep geoscience computing
\end{keywords}
\ExplSyntaxOn
\keys_set:nn { stm / mktitle } { nologo=true }
\ExplSyntaxOff
\begingroup
\hfuzz=120pt
\maketitle
\endgroup
\hypersetup{
  pdftitle={Trustworthy Borehole Database Ingestion from VLM Proposals: Provenance and Spatial Support},
  pdfauthor={Yifan Du},
  pdfsubject={Provenance-grounded selective assurance for borehole database ingestion},
  pdfkeywords={borehole logs, vision-language models, provenance, selective prediction, spatial support, geoscience computing},
  pdfinfo={Paper4SourceSHA256={""" + source_sha256 + r"""}}
}
\printcredits
\doublespacing
""" + review_box + r"""
\section*{Highlights}
\begin{itemize}
""" + highlights_block + r"""
\end{itemize}
"""

    review_note = r"""
\clearpage
\section*{Questions for Academic Review}
\begin{enumerate}[leftmargin=*]
\item Is the central scientific question sufficiently strong for Computers \& Geosciences?
\item Is the computer-science contribution clear beyond an engineering pipeline?
\item Are any claims overstated relative to the evidence?
\item Are any essential experiments missing before submission?
\item Is the downstream spatial-support argument convincing and appropriately limited?
\end{enumerate}
    \textit{This page is for internal academic review only and must be removed from any formal submission manuscript.}
\end{document}
"""
    if final_mode:
        review_note = r"""\end{document}
"""

    table3_tex, table4_tex, table5_tex = tables_tex()
    table3_md, table4_md, table5_md = tables_markdown()
    body = body.replace(
        "The paired document-cluster F1 gains of Qwen over RapidOCR are 0.542, 0.445, 0.535, 0.489, and 0.514; every bootstrap probability that the gain is positive is 1.000.",
        "The paired document-cluster F1 gains of Qwen over RapidOCR are 0.542, 0.445, 0.535, 0.489, and 0.514; every bootstrap probability that the gain is positive is 1.000. Figure~\\ref{fig:capability} and Table~\\ref{tab:reliability} report the same F1 results.",
    )
    body = body.replace(
        "Finding a number is therefore easier than proving interval ownership.",
        "Finding a number is therefore easier than proving interval ownership. Figure~\\ref{fig:assurance} visualizes the operating point and evidence funnel; Table~\\ref{tab:assurance} reports the corresponding values.",
    )
    body = body.replace(
        "The overlap is more scientifically informative than the ordering of three full-data estimates.",
        "The overlap is more scientifically informative than the ordering of three full-data estimates. Figure~\\ref{fig:spatial} contrasts the estimands, and Table~\\ref{tab:spatial} reports the corresponding diagnostics.",
    )
    body = body.replace("shown in Fig. 1:", "shown in Fig.~\\ref{fig:framework}:")
    body = body.replace(
        "The evaluation separates evidence types before any metric is calculated.",
        "The evaluation separates evidence types before any metric is calculated; Table~\\ref{tab:evidence-tiers} defines the tiers used here.",
    )
    body = body.replace(
        "database, and what observational support is lost when it is not admitted.",
        "database, and what observational support is lost when it is not admitted. Table~\\ref{tab:related-work} summarizes the representative-work comparison.",
    )
    body = add_longtable_continuation_caption(
        body,
        "tab:related-work",
        "Representative-work comparison",
    )
    body = add_longtable_continuation_caption(
        body,
        "tab:evidence-tiers",
        "Evidence tiers and supported claims",
    )
    for digest in (
        "74227dd615bf1ea975aa676bdf355a0379858c12f394b5365cd9dfa5fc2c70bc",
        "27225450ac9c6529872ee1924fcb0962ff5634834f817040f444118116f4e516",
        "f0838c766951bdfe76d6afbdb2771a8f67aaa2231dedb3d33cebd817729843a2",
        "891bc6beb7ff9cf35c55389191a208c9b09e9e2dc76909f716603f413745104a",
    ):
        body = body.replace(r"\path{" + digest + "}", r"\hash{" + digest + "}")
    body = insert_after_latex_figure(body, "figures/Figure_2.pdf", table3_tex)
    body = insert_after_latex_figure(body, "figures/Figure_3.pdf", table4_tex)
    body = insert_after_latex_figure(body, "figures/Figure_4.pdf", table5_tex)
    manuscript = header + body + r"""
\bibliographystyle{cas-model2-names}
\bibliography{references_cageo}
""" + review_note
    (HERE / "manuscript.tex").write_text(manuscript, encoding="utf-8", newline="\n")
    if final_mode:
        final_md = source.replace(
            "# " + TITLE,
            "# " + TITLE + "\n\n**Author:** Yifan Du\\\n**Affiliation:** North China University of Water Resources and Electric Power, Zhengzhou, Henan 450046, China\\\n**Corresponding author:** Yifan Du (duyifan619916@gmail.com)\\\n**ORCID:** 0009-0008-7740-5408\n\n**CRediT author statement:** Conceptualization; Data curation; Formal analysis; Investigation; Methodology; Project administration; Resources; Software; Validation; Visualization; Writing -- original draft; Writing -- review and editing.",
            1,
        )
        final_md = re.sub(r"\n\*\*Table 3\.\*\*.*?(?=\n## Computer Code Availability)", "\n", final_md, flags=re.S)
        final_md = insert_after_markdown_figure(final_md, "figures/F2_vlm_source_shift.png", table3_md)
        final_md = insert_after_markdown_figure(final_md, "figures/F3_assurance_frontier.png", table4_md)
        final_md = insert_after_markdown_figure(final_md, "figures/F4_spatial_support_consequence.png", table5_md)
        final_md = re.sub(r"## References\s*$", markdown_references(bibliography), final_md, flags=re.S)
        (HERE / "manuscript_final.md").write_text(final_md, encoding="utf-8", newline="\n")
    print(f"wrote {HERE / 'manuscript.tex'}")
    print(f"wrote {HERE / 'references_cageo.bib'} with {len(cited_keys)} cited entries")
    print(f"word_count_main={main_words}")


if __name__ == "__main__":
    main()
