#!/usr/bin/env python3
"""Build the Paper 4 Computers & Geosciences internal review manuscript.

The scientific Markdown remains the source of truth. This script only
formats a review artifact and asserts that frozen headline values are still
present before emitting the LaTeX source.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
PAPER = REPO / "papers" / "paper4"


TITLE = (
    "Trustworthy Borehole Database Ingestion from VLM Proposals: "
    "Provenance and Spatial Support"
)


ABSTRACT = r"""\textbf{Background:} High visual extraction accuracy does not by itself establish a trustworthy geological database. A database row also needs independently checkable page evidence, a decision state, and an account of what abstention removes from downstream spatial support. \textbf{Methods:} We evaluate the frozen \texttt{Qwen/Qwen3.8-27B-FP8} direct page-to-JSON reader on five record-disjoint California cohorts (450 reports; 8,268 published manual-transcription intervals) and source-shift panels. The headline metric is boundary-pair interval F1: both interval depths must match under an order-preserving tolerance. We then add an independently positioned reader, deterministic depth/column checks, and an accept-or-review policy; a separate legacy sequence-reconstruction analysis is reported only as a harm analysis. \textbf{Results:} Qwen reaches boundary-pair F1 0.896--0.932 on California, but falls to 0.577 on the Swissgeol source-agreement panel. On held-out California v003, independent evidence yields accepted-interval precision 0.993 (444/447 accepted intervals correct) at 0.244 proposal coverage. Only 4/100 documents satisfy complete-document auto-acceptance, which defines a conservative deployment boundary rather than a claim of full automation. A spatial diagnostic shows that full-support risk-aware volume discrepancy is 0.0821 versus 0.1387 for raw extraction, while retaining only 0.636 of the reference convex-hull area; on the identical 15-document accepted subset, risk and rereading are both 0.0754 versus 0.0326 for raw. \textbf{Conclusions:} Modern VLMs are strong proposal readers, not database authorities. Provenance-grounded selective decisions must report precision together with coverage, complete-document utility, review burden, and the spatial-support consequences of abstention."""


HIGHLIGHTS = [
    "Qwen3.8-27B-FP8 reaches 0.896--0.932 boundary-pair F1 on 450 reports.",
    "Independent evidence reaches 0.993 precision at 24.4% proposal coverage.",
    "Only 4% of held-out documents qualify for complete automatic acceptance.",
    "Abstention changes spatial support and can reverse apparent improvement.",
]


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
    body = replace_sections(body)
    body = body.replace(
        r"Fixed ACCEPT/NEEDS\_REVIEW",
        r"\makecell[l]{Fixed\\ACCEPT/\\NEEDS\_\\REVIEW}",
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
    body = body.replace(r"(V=(v\_1,ldots,v\_n))", r"\(V=(v_1,\ldots,v_n)\)")
    body = body.replace(r"(C=(c\_1,ldots,c\_m))", r"\(C=(c_1,\ldots,c_m)\)")
    body = body.replace(
        r"For (n) accepted documents and zero observed worsened documents, the one-sided 95\% upper bound is (1-0.05\^{}\{1/n\});",
        r"For \(n\) accepted documents and zero observed worsened documents, the one-sided 95\% upper bound is \(1 - 0.05^{1/n}\);",
    )

    # The Markdown math delimiters are intentionally rewritten explicitly so
    # equations remain editable and are not treated as literal punctuation by
    # the Markdown-to-LaTeX converter.
    spatial_start = body.find("For boundary (r) in borehole (i)")
    spatial_end = body.find("\n\nWe report two estimands.", spatial_start)
    if spatial_start >= 0 and spatial_end > spatial_start:
        spatial = r"""For boundary \(r\) in borehole \(i\), elevation is \(z_{ir}=c_i-d_{ir}\), where \(c_i\) is collar elevation and \(d_{ir}\) is depth. IDW at query location \(u\) is

\begin{equation}
\hat z_r(u)=\frac{\sum_{i\in N(u)}\lVert u-u_i\rVert^{-p}z_{ir}}{\sum_{i\in N(u)}\lVert u-u_i\rVert^{-p}}.
\end{equation}

Thickness is the difference between adjacent surfaces. For a hull-clipped grid \(G\), the volume diagnostic is

\begin{equation}
\hat V_\ell=A|G|^{-1}\sum_{u\in G}\hat h_\ell(u),
\end{equation}

and the aggregate reference-relative volume discrepancy is

\begin{equation}
\frac{\sum_\ell|\hat V_\ell-V_\ell|}{\sum_\ell|V_\ell|}.
\end{equation}"""
        body = body[:spatial_start] + spatial + body[spatial_end:]

    body = body.replace(
        "The direct-VLM baseline, positioned parser, sequence decoder, risk policy, and spatial diagnostics are deterministic given the frozen page renders, candidate pools, configuration files, and seeds.",
        "The evaluation protocol and deterministic post-processing components were frozen. The VLM used fixed decoding settings, while bitwise deterministic execution is not claimed.",
    )
    body = body.replace(
        "Source PDFs and transformed inputs are distributed under the project release policy; provenance and final rights checks remain explicit in the ledger.",
        "Only redistributable structured/reanalysis assets, manifests, hashes, source URLs, and recomputation materials are released. Source PDFs and page-derived assets remain excluded where item-level redistribution rights are unresolved.",
    )
    body = body.replace(
        "\\caption{Figure 1. Provenance-grounded assurance framework.}",
        "\\caption{Provenance-grounded assurance framework. VLM proposals are checked against independent positioned evidence and deterministic geometry before acceptance or review.}",
    )
    body = body.replace(
        "\\caption{Figure 2. Modern VLM reliability across California cohorts and source shift.}",
        "\\caption{Modern VLM reliability across California cohorts and source shift. California cohort results and source-agreement transfer outcomes are shown with their declared evidence tiers.}",
    )
    body = body.replace(
        "\\caption{Figure 3. Selective assurance viewed simultaneously as precision, proposal coverage, complete-document automation, and a held-out v003 evidence funnel. Numeric anchors are reported separately as endpoint-field coverage (3,099/3,666) and as both-endpoint interval coverage (1,450/1,833); only semantically owned intervals are accepted.}",
        "\\caption{Selective assurance operating point. Precision, proposal coverage, complete-document automation, and held-out v003 evidence are shown together. Endpoint-field anchors are 3,099/3,666, both-endpoint interval anchors are 1,450/1,833, and semantically owned accepted intervals are 447/1,833.}",
    )
    body = body.replace(
        "\\caption{Figure 4. Full-support versus matched-support downstream consequence of selective acceptance.}",
        "\\caption{Full-support and matched-support downstream consequences. Full-support and matched-support are distinct estimands; matched-support results use the identical 15 accepted documents.}",
    )

    # Make unresolved declarations explicit in a review artifact rather than
    # silently treating generic source text as final metadata.
    body = re.sub(
        r"(\\section\*\{Computer Code Availability\}.*?\n\n).*?(?=\\section\*\{Data Availability\})",
        r"\1The GeoLogParser repository contains versioned code/configuration, prompt hashes, metric bindings, and scripts that regenerate Paper 4 tables, figures, claim audits, and redistributable reanalysis assets.\\par\n\\textbf{Review metadata:} Public URL, license, archival identifier, and release commit: [TO BE ARCHIVED BEFORE SUBMISSION].",
        body,
        flags=re.S,
    )
    body = re.sub(
        r"(\\section\*\{Data Availability\}.*?\n\n).*?(?=\\section\*\{Declarations\})",
        r"\1Only redistributable structured/reanalysis assets, manifests, hashes, source URLs, and recomputation materials are released. Source PDFs and page-derived assets remain excluded where item-level redistribution rights are unresolved.\\par\n\\textbf{Review metadata:} Final data repository/DOI and item-level rights, attribution, linkage, privacy, and sensitive-location review: [TO BE CONFIRMED].",
        body,
        flags=re.S,
    )
    body = re.sub(
        r"(\\section\*\{Declarations\}.*?\n\n).*?(?=\\section\*\{References\})",
        r"\1\\textbf{Authorship and CRediT:} [TO BE CONFIRMED].\\par\n\\textbf{Funding:} [TO BE CONFIRMED].\\par\n\\textbf{Competing interests:} [TO BE CONFIRMED].\\par\n\\textbf{Generative AI disclosure:} [TO BE CONFIRMED BEFORE SUBMISSION].\\par\n\\textbf{Rights clearance:} [PENDING FINAL HUMAN REVIEW].",
        body,
        flags=re.S,
    )
    # Replace the generic source declarations with the author-confirmed
    # submission statements after the review-era normalization above.
    body = re.sub(
        r"\\section\*\{Computer Code Availability\}.*?(?=\\section\*\{Data Availability\})",
        r"\\section*{Computer Code Availability}\nThe GeoLogParser repository contains versioned code/configuration, prompt hashes, metric bindings, and scripts that regenerate Paper 4 tables, figures, claim audits, and redistributable reanalysis assets.\\par\n\\textbf{Repository:} \\url{https://github.com/Entropic-Silence/GeoLogParser}.\\par\n\\textbf{License:} MIT for source code.\\par\n\\textbf{Version:} final branch commit is recorded in the submission artifact manifest; no archival DOI has yet been minted.\n",
        body,
        flags=re.S,
    )
    body = re.sub(
        r"\\section\*\{Data Availability\}.*?(?=\\section\*\{Declarations\})",
        r"\\section*{Data Availability}\nAll public structured/reanalysis assets and materials needed to reproduce the reported analyses are available in the GeoLogParser repository, including manifests, hashes, source URLs, model configurations, and recomputation scripts. Source PDFs, rendered pages, raw OCR regions, and model weights are not redistributed where third-party terms apply; the repository preserves retrieval and attribution metadata for authorized access.\\par\n\\textbf{Persistent identifier:} The GitHub repository is the public data/code record; an archival DOI remains an author action before formal submission.\n",
        body,
        flags=re.S,
    )
    body = re.sub(
        r"\\section\*\{Declarations\}.*?(?=\\section\*\{References\})",
        r"\\section*{Declarations}\n\\textbf{Authorship and CRediT:} Yifan Du is the sole author and corresponding author. Roles: Conceptualization; Data curation; Formal analysis; Funding acquisition; Investigation; Methodology; Project administration; Resources; Software; Supervision; Validation; Visualization; Writing -- original draft; Writing -- review and editing.\\par\n\\textbf{Funding:} This research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit sectors; it was self-funded.\\par\n\\textbf{Competing interests:} The author declares no competing interests.\\par\n\\textbf{Declaration of generative AI and AI-assisted technologies in the manuscript preparation process:} During preparation of this manuscript, ChatGPT (OpenAI) was used to assist with repository assembly, formatting, and language editing. The author reviewed and takes full responsibility for the accuracy, originality, and integrity of the published work; no model, experiment, result, or scientific interpretation was delegated to the tool.\\par\n\\textbf{Rights and linkage:} Public and reproducibility materials are linked from the repository; source-specific attribution and redistribution restrictions are retained in the release ledger.\n",
        body,
        flags=re.S,
    )
    body = re.sub(r"Shared bibliography:.*?(?:\n|$)", "", body)
    body = re.sub(r"\\section\*\\?\{References\}(?:\\label\{references\})?", "", body)
    return body


def tables_tex() -> str:
    return r"""
\clearpage
\section*{Main Results Tables}
\addcontentsline{toc}{section}{Main Results Tables}

\begin{table}
\centering
\scriptsize
\caption{Reliability across cohorts and source families. Evidence tiers are not pooled.}
\label{tab:reliability}
\resizebox{\textwidth}{!}{%
\begin{tabular}{@{}llllrrrr@{}}
\toprule
Cohort/source & Evidence & Documents & Intervals & System & F1 & Boundary-exact & Zero output \\
\midrule
California v001 & Published manual transcription Gold & 50 & 697 & Qwen direct & 0.932 & 0.740 & 0.000 \\
California v002 & Published manual transcription Gold & 100 & 1,770 & Qwen direct & 0.896 & 0.700 & 0.000 \\
California v003 & Published manual transcription Gold & 100 & 1,788 & Qwen direct & 0.918 & 0.720 & 0.000 \\
California v004 & Published manual transcription Gold & 100 & 1,944 & Qwen direct & 0.917 & 0.740 & 0.050 \\
California v005 & Published manual transcription Gold & 100 & 2,069 & Qwen direct & 0.903 & 0.690 & 0.010 \\
Swissgeol Thurgau held-out & Source-agreement reference & 35 & 80 & Qwen direct & 0.577 & 0.000 & 0.000 \\
BGS Offshore & Source-agreement reference & 26 & 341 & RapidOCR positioned & 0.038 & -- & -- \\
\bottomrule
\end{tabular}}
\end{table}

\begin{table}
\centering
\scriptsize
\caption{Independent evidence and selective assurance. Endpoint-field and interval-level anchor coverage are distinct quantities.}
\label{tab:assurance}
\resizebox{\textwidth}{!}{%
\begin{tabular}{@{}lrrrrrrr@{}}
\toprule
Cohort & Raw precision & Endpoint-field anchor & Both endpoints anchored & Owned/accepted & Accepted intervals & Selective precision (95\% CI) & Error documents \\
\midrule
California v001 development & 0.908 & 0.817 & 0.731 & 0.236 & 174 & 1.000 [1.000, 1.000] & 0 \\
California v002 validation & 0.854 & 0.849 & 0.792 & 0.287 & 561 & 0.979 [0.951, 0.997] & 5 \\
California v003 held-out & 0.907 & 0.845 & 0.791 & 0.244 & 447 & 0.993 [0.984, 1.000] & 3 \\
\bottomrule
\end{tabular}}
\end{table}

\begin{table}
\centering
\small
\caption{Risk, coverage, and downstream support diagnostics.}
\label{tab:spatial}
\begin{tabular}{@{}lrrr@{}}
\toprule
Analysis & Raw & Reread & Risk-aware \\
\midrule
Full-support volume discrepancy & 0.1387 & 0.1213 & 0.0821 \\
Matched-subset volume discrepancy & 0.0326 & 0.0754 & 0.0754 \\
First-boundary hull-area ratio & 1.000 & 1.000 & 0.636 \\
Default LOO MAE (m) & 49.84 & 46.62 & 47.05 \\
\bottomrule
\end{tabular}
\end{table}

"""


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
    body_lines = [line for line in body.splitlines() if not line.lstrip().startswith("|")]
    body_no_tables = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", "\n".join(body_lines))
    keywords = source.split("**Keywords:**", 1)[1].split("\n", 1)[0]
    highlights = "\n".join(line[2:] for line in source.split("## Highlights", 1)[1].split("## 1.", 1)[0].splitlines() if line.startswith("- "))
    count = lambda text: len(re.findall(r"\b[\w'-]+\b", text))
    return count(abstract), count(body_no_tables), count(body), count(keywords) + count(highlights)


def main() -> None:
    final_mode = "--final" in sys.argv[1:]
    body_path = HERE / "body_pandoc.tex"
    positional = [arg for arg in sys.argv[1:] if arg != "--final"]
    if positional:
        body_path = Path(positional[0]).resolve()
    source = (PAPER / "manuscript.md").read_text(encoding="utf-8")
    for frozen in FROZEN_STRINGS:
        if frozen not in source:
            raise ValueError(f"Frozen source check failed: {frozen}")
    body = body_path.read_text(encoding="utf-8")
    start = body.find(r"\subsection{1. Problem, hypothesis, and research questions}")
    if start < 0:
        raise ValueError("Pandoc body does not contain the expected Introduction heading")
    body = repair_body(body[start:])

    cited_keys = sorted(set(re.findall(r"@([A-Za-z0-9_:-]+)", source)))
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

    for index, highlight in enumerate(HIGHLIGHTS, 1):
        print(f"highlight_{index}_characters={len(highlight)}")
        if len(highlight) > 85:
            raise ValueError(f"Highlight {index} exceeds 85 characters")

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

    header = rf"""{preamble_note}
%% Scientific content is retained from papers/paper4/manuscript.md.
\documentclass[a4paper,fleqn]{{cas-sc}}
\usepackage[authoryear]{{natbib}}
\usepackage{{graphicx}}
\usepackage{{float}}
\usepackage{{setspace}}
\usepackage{{lineno}}
\usepackage{{longtable}}
\usepackage{{booktabs}}
\usepackage{{array}}
\usepackage{{tabularx}}
\usepackage{{calc}}
\usepackage{{adjustbox}}
\usepackage{{seqsplit}}
\usepackage{{xcolor}}
\usepackage{{enumitem}}
\usepackage{{microtype}}
\hypersetup{{hypertexnames=false}}
\newcommand{{\pandocbounded}}[1]{{#1}}
\newcommand{{\tightlist}}{{}}
\newcommand{{\real}}[1]{{#1}}
\newcommand{{\hash}}[1]{{\texttt{{\seqsplit{{#1}}}}}}
\newcolumntype{{Y}}{{>{{\raggedright\arraybackslash}}X}}
\graphicspath{{{{../../}}}}
\setlength{{\emergencystretch}}{{3em}}
\linenumbers
\begin{{document}}
{footer_definition}
\let\WriteBookmarks\relax
\shorttitle{{{shorttitle}}}
\shortauthors{{{shortauthors}}}
\title[mode=title]{{{TITLE}}}
\author[1]{{Yifan Du}}[auid=000,orcid=0009-0008-7740-5408]
\cormark[1]
\ead{{duyifan619916@gmail.com}}
\credit{{Conceptualization; Data curation; Formal analysis; Funding acquisition; Investigation; Methodology; Project administration; Resources; Software; Supervision; Validation; Visualization; Writing -- original draft; Writing -- review and editing}}
\address[1]{{North China University of Water Resources and Electric Power, Zhengzhou, Henan 450046, China}}
\begingroup
\ExplSyntaxOn
\cs_set:Npn \msg_term:n #1 {{}}
\ExplSyntaxOff
\cortext[cor1]{{Corresponding author.}}
\endgroup
\begin{{abstract}}
{ABSTRACT}
\end{{abstract}}
"""
    highlights_block = "\n".join(
        "\\item " + highlight.replace("%", "\\%") for highlight in HIGHLIGHTS
    )
    header += r"""
\begin{keywords}
borehole logs \sep vision-language models \sep provenance \sep selective prediction \sep spatial support \sep geoscience computing
\end{keywords}
\ExplSyntaxOn
\keys_set:nn { stm / mktitle } { nologo=true }
\ExplSyntaxOff
\maketitle
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

    tables = tables_tex()
    body = body.replace(
        "The paired document-cluster F1 gains of Qwen over RapidOCR are 0.542, 0.445, 0.535, 0.489, and 0.514; every bootstrap probability that the gain is positive is 1.000.",
        "The paired document-cluster F1 gains of Qwen over RapidOCR are 0.542, 0.445, 0.535, 0.489, and 0.514; every bootstrap probability that the gain is positive is 1.000. Results are summarized in Table~\\ref{tab:reliability}.",
    )
    body = body.replace(
        "Finding a number is therefore easier than proving interval ownership.",
        "Finding a number is therefore easier than proving interval ownership. Table~\\ref{tab:assurance} reports the operating point.",
    )
    body = body.replace(
        "The overlap is more scientifically informative than the ordering of three full-data estimates.",
        "The overlap is more scientifically informative than the ordering of three full-data estimates (Table~\\ref{tab:spatial}).",
    )
    for digest in (
        "74227dd615bf1ea975aa676bdf355a0379858c12f394b5365cd9dfa5fc2c70bc",
        "27225450ac9c6529872ee1924fcb0962ff5634834f817040f444118116f4e516",
        "f0838c766951bdfe76d6afbdb2771a8f67aaa2231dedb3d33cebd817729843a2",
        "891bc6beb7ff9cf35c55389191a208c9b09e9e2dc76909f716603f413745104a",
    ):
        body = body.replace(r"\path{" + digest + "}", r"\hash{" + digest + "}")
    body_before_code, body_code = body.split(r"\section*{Computer Code Availability}", 1)
    body = body_before_code + tables + r"\section*{Computer Code Availability}" + body_code
    manuscript = header + body + r"""
\bibliographystyle{cas-model2-names}
\bibliography{references_cageo}
""" + review_note
    (HERE / "manuscript.tex").write_text(manuscript, encoding="utf-8", newline="\n")
    if final_mode:
        credit_roles = (
            "Conceptualization; Data curation; Formal analysis; Funding acquisition; "
            "Investigation; Methodology; Project administration; Resources; Software; "
            "Supervision; Validation; Visualization; Writing -- original draft; "
            "Writing -- review and editing"
        )
        final_md = source.replace(
            "# " + TITLE,
            "# " + TITLE + "\n\n**Author:** Yifan Du\\\n**Affiliation:** North China University of Water Resources and Electric Power, Zhengzhou, Henan 450046, China\\\n**Corresponding author:** Yifan Du (duyifan619916@gmail.com)\\\n**ORCID:** 0009-0008-7740-5408",
            1,
        )
        final_md = re.sub(
            r"## Computer Code Availability.*?## Data Availability",
            "## Computer Code Availability\n\nThe GeoLogParser source code, configurations, manifests, figure generators, claim audits, and reproducibility scripts are publicly available at https://github.com/Entropic-Silence/GeoLogParser under the MIT license. The final branch commit is recorded in the submission artifact manifest; no archival DOI has yet been minted.\n\n## Data Availability",
            final_md,
            flags=re.S,
        )
        final_md = re.sub(
            r"## Data Availability.*?## Declarations",
            "## Data Availability\n\nAll public structured/reanalysis assets and materials needed to reproduce the reported analyses are available in the GeoLogParser repository. Source PDFs, rendered pages, raw OCR regions, and model weights are not redistributed where third-party terms apply; retrieval, attribution, and linkage metadata are retained. An archival DOI remains an author action before formal submission.\n\n## Declarations",
            final_md,
            flags=re.S,
        )
        final_md = re.sub(
            r"## Declarations.*?## References",
            "## Declarations\n\n**Authorship and CRediT:** Yifan Du is the sole author and corresponding author. Roles: " + credit_roles + ".\n\n**Funding:** This research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit sectors; it was self-funded.\n\n**Competing interests:** The author declares no competing interests.\n\n**Declaration of generative AI and AI-assisted technologies in the manuscript preparation process:** During preparation of this manuscript, ChatGPT (OpenAI) was used to assist with repository assembly, formatting, and language editing. The author reviewed and takes full responsibility for the accuracy, originality, and integrity of the published work; no model, experiment, result, or scientific interpretation was delegated to the tool.\n\n**Rights and linkage:** Public and reproducibility materials are linked from the repository; source-specific attribution and redistribution restrictions are retained in the release ledger.\n\n## References",
            final_md,
            flags=re.S,
        )
        (HERE / "manuscript_final.md").write_text(final_md, encoding="utf-8", newline="\n")
    print(f"wrote {HERE / 'manuscript.tex'}")
    print(f"wrote {HERE / 'references_cageo.bib'} with {len(cited_keys)} cited entries")
    print(f"word_count_main={main_words}")


if __name__ == "__main__":
    main()
