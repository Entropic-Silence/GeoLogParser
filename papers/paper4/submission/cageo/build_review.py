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

RELEASE_TAG = "paper4-cageo-v1.0.7"
ARTICLE_DOI = "10.5281/zenodo.22030229"
DATA_DOI = "10.5281/zenodo.22031703"


ABSTRACT = r"""\textbf{Background:} High visual extraction accuracy does not by itself establish a trustworthy geological database. A database row also needs independently checkable page evidence, a decision state, and an account of what abstention removes from downstream spatial support. \textbf{Methods:} We evaluate the frozen \texttt{Qwen/Qwen3.8-27B-FP8} direct page-to-JSON reader on five record-disjoint California cohorts (450 reports; 8,268 published manual-transcription intervals) and source-shift panels. The headline metric is boundary-pair interval F1: both interval depths must match under an order-preserving tolerance. We then add an independently positioned reader, deterministic depth/column checks, and an accept-or-review policy; a separate legacy sequence-reconstruction analysis is reported only as a harm analysis. \textbf{Results:} Qwen reaches boundary-pair F1 0.896--0.932 on California, but falls to 0.577 on the Swissgeol source-agreement panel. On held-out California v003, independent evidence yields accepted-interval precision 0.993 (444/447 accepted intervals correct) at 0.244 proposal coverage. Only 4/100 documents satisfy complete-document auto-acceptance, which defines a conservative deployment boundary rather than a claim of full automation. A spatial diagnostic shows that full-support risk-aware volume discrepancy is 0.0821 versus 0.1387 for raw extraction, while retaining only 0.636 of the reference convex-hull area; on the identical 15-document accepted subset, risk and rereading are both 0.0754 versus 0.0326 for raw. \textbf{Conclusions:} Modern VLMs are strong proposal readers, not database authorities. Provenance-grounded selective decisions must report precision together with coverage, complete-document utility, review burden, and the spatial-support consequences of abstention."""


HIGHLIGHTS = [
    "Qwen3.8-27B-FP8 reaches 0.896--0.932 boundary-pair F1 on 450 reports.",
    "Independent evidence reaches 0.993 precision at 24.4% proposal coverage.",
    "Only 4% of held-out documents qualify for complete automatic acceptance.",
    "Abstention changes spatial support and can reverse apparent improvement.",
]


CODE_AVAILABILITY = (
    "Program title: GeoLogParser Paper 4 result-reproduction package. Developer and "
    "contact: Yifan Du, duyifan619916@gmail.com. First public availability: 2026. "
    "The package contains versioned code/configuration, prompt hashes, metric bindings, "
    "figure generators, claim audits, and recomputation scripts for this article. "
    "The source code is released under the MIT license at "
    "https://github.com/Entropic-Silence/GeoLogParser. It is written primarily in "
    "Python and uses the frozen JSON/JSONL inputs; the deterministic result-level "
    "workflow requires Python 3.10 or newer and standard scientific Python packages. "
    "The final tagged package is paper4-cageo-v1.0.7. The optional VLM/OCR execution "
    "environment, weights, and private credentials are not redistributed; the package "
    "reproduces frozen predictions through the matcher, metrics, tables, figures, and "
    "audits. The public repository and release assets are the access method. Article DOI: "
    "https://doi.org/10.5281/zenodo.22030229. Data companion DOI: "
    "https://doi.org/10.5281/zenodo.22031703."
)


CODE_AVAILABILITY_TEX = (
    r"\\section*{Computer Code Availability}\n"
    r"Program title: GeoLogParser Paper 4 result-reproduction package. "
    r"Developer and contact: Yifan Du, \\href{mailto:duyifan619916@gmail.com}{duyifan619916@gmail.com}. "
    r"First public availability: 2026. The package contains versioned code/configuration, "
    r"prompt hashes, metric bindings, figure generators, claim audits, and recomputation "
    r"scripts for this article. The source code is released under the MIT license at "
    r"\\url{https://github.com/Entropic-Silence/GeoLogParser}. It is written primarily in "
    r"Python and uses frozen JSON/JSONL inputs; the deterministic result-level workflow "
    r"requires Python 3.10 or newer and standard scientific Python packages. The final "
    r"tagged package is \\texttt{paper4-cageo-v1.0.7}. The optional VLM/OCR execution "
    r"environment, weights, and private credentials are not redistributed; the package "
    r"reproduces frozen predictions through the matcher, metrics, tables, figures, and "
    r"audits. The public repository and release assets are the access method. Article DOI: "
    r"\\url{https://doi.org/10.5281/zenodo.22030229}. Data companion DOI: "
    r"\\url{https://doi.org/10.5281/zenodo.22031703}.\\par\n"
)

DATA_AVAILABILITY = (
    "The paper4-cageo-v1.0.7 package contains the manuscript, supplement, figures, "
    "structured/reanalysis inputs, aggregate metrics, manifests, checksums, source URLs, "
    "and recomputation scripts needed to reproduce the reported result-level analyses. "
    "The separate data-v002 companion contains the author-reviewed selected source files "
    "and structured datasets used by the principal experiments; it is a data companion, "
    "not the complete Paper 4 package. Source-specific terms and attribution remain in "
    "the release ledger, and linkable spatial inputs are not represented as anonymous. "
    "Model weights and private credentials are not redistributed. The article package "
    "has the reserved DOI https://doi.org/10.5281/zenodo.22030229 and the separate data "
    "companion has the reserved DOI https://doi.org/10.5281/zenodo.22031703. The records "
    "remain unpublished until the author registers them. The data archive has mixed "
    "source-specific rights and no blanket licence; see its DATA_LICENSES.md and ledger."
)


DECLARATIONS = (
    "**Funding:** This research did not receive any specific grant from funding agencies "
    "in the public, commercial, or not-for-profit sectors; it was self-funded.\n\n"
    "**Competing interests:** The author declares no competing interests.\n\n"
    "**Rights and linkage sign-off:** Yifan Du, sole and corresponding author, confirms that the "
    "paper4-cageo-v1.0.7 package and exact data-v002 selection were reviewed for public "
    "dissemination; the data review covered source terms, selected item scope, privacy, "
    "sensitive locations, embedded third-party content, attribution, and linkage. "
    "This sign-off supersedes earlier provisional ledger statuses for the named release "
    "scope; historical experiment-run metadata remains historical. Source-specific "
    "obligations are retained in the manifests and ledger. This item-"
    "scoped sign-off does not grant a blanket licence to unrelated repository sources.\n\n"
    "No claim in this manuscript relies on undisclosed human annotation, hidden "
    "reference-conditioned tuning, or a closed-model score that lacks a reproducible "
    "execution record."
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
    body = body.replace(r"(V=(v\_1,ldots,v\_n))", r"\(V=(v_1,\ldots,v_n)\)")
    body = body.replace(r"(C=(c\_1,ldots,c\_m))", r"\(C=(c_1,\ldots,c_m)\)")
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
        "The article package releases structured/reanalysis assets, manifests, hashes, source URLs, and recomputation materials. The separately versioned data-v002 companion contains the selected source files and structured datasets that passed the author's item-level rights, attribution, linkage, privacy, sensitive-location, and embedded-content review. Model weights and private credentials are not redistributed.",
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
    # Replace source availability and declaration sections with the
    # author-confirmed submission statements.
    body = re.sub(
        r"\\section\*\{Computer Code Availability\}.*?(?=\\section\*\{Data Availability\})",
        CODE_AVAILABILITY_TEX,
        body,
        flags=re.S,
    )
    body = re.sub(
        r"\\section\*\{Data Availability\}.*?(?=\\section\*\{Declarations\})",
        r"\\section*{Data Availability}\nThe \\texttt{paper4-cageo-v1.0.7} package contains the manuscript, supplement, figures, structured/reanalysis inputs, aggregate metrics, manifests, checksums, source URLs, and recomputation scripts needed to reproduce the reported result-level analyses. The separate \\texttt{data-v002} companion contains the author-reviewed selected source files and structured datasets used by the principal experiments; it is a data companion, not the complete Paper 4 package. Source-specific terms and attribution remain in the release ledger, and linkable spatial inputs are not represented as anonymous. Model weights and private credentials are not redistributed. The article package has reserved DOI \\url{https://doi.org/10.5281/zenodo.22030229}; the data companion has reserved DOI \\url{https://doi.org/10.5281/zenodo.22031703}. The records remain unpublished until the author registers them. The data archive has mixed source-specific rights and no blanket licence; see its \\texttt{DATA\\_LICENSES.md} and ledger.\n",
        body,
        flags=re.S,
    )
    body = re.sub(
        r"\\section\*\{Declarations\}.*?(?=\\section\*\{References\})",
        r"\\section*{Declarations}\n\\textbf{Funding:} This research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit sectors; it was self-funded.\\par\n\\textbf{Competing interests:} The author declares no competing interests.\\par\n\\textbf{Rights and linkage sign-off:} Yifan Du, sole and corresponding author, confirms that the \\texttt{paper4-cageo-v1.0.7} package and exact \\texttt{data-v002} selection were reviewed for public dissemination; the data review covered source terms, selected item scope, privacy, sensitive locations, embedded third-party content, attribution, and linkage. This sign-off supersedes earlier provisional ledger statuses for the named release scope; historical experiment-run metadata remains historical. Source-specific obligations are retained in the manifests and ledger. This item-scoped sign-off does not grant a blanket licence to unrelated repository sources.\\par\n\\textbf{Reproducibility scope:} No claim in this manuscript relies on undisclosed human annotation, hidden reference-conditioned tuning, or a closed-model score that lacks a reproducible execution record.\n",
        body,
        flags=re.S,
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
  pdfkeywords={{borehole logs, vision-language models, provenance, selective prediction, spatial support}}
}}
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
\credit{{Conceptualization; Data curation; Formal analysis; Investigation; Methodology; Project administration; Resources; Software; Validation; Visualization; Writing -- original draft; Writing -- review and editing}}
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
\begingroup
\hfuzz=120pt
\maketitle
\endgroup
\hypersetup{
  pdftitle={Trustworthy Borehole Database Ingestion from VLM Proposals: Provenance and Spatial Support},
  pdfauthor={Yifan Du},
  pdfsubject={Provenance-grounded selective assurance for borehole database ingestion},
  pdfkeywords={borehole logs, vision-language models, provenance, selective prediction, spatial support}
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
    body = body.replace(
        "\\caption{Modern VLM reliability across California cohorts and source shift. California cohort results and source-agreement transfer outcomes are shown with their declared evidence tiers.}",
        "\\caption{Modern VLM reliability across California cohorts and source shift. The familiar-source panel compares Qwen3.8-27B-FP8 with the positioned RapidOCR parser on five record-disjoint California cohorts with published manual-transcription Gold evidence. The source-shift panel reports Swissgeol, British Geological Survey (BGS), and Raft River transfer/stress outcomes with their declared evidence tiers; these values are not pooled with California Gold.}",
    )
    body = body.replace(
        "\\caption{Selective assurance operating point. Precision, proposal coverage, complete-document automation, and held-out v003 evidence are shown together. Endpoint-field anchors are 3,099/3,666, both-endpoint interval anchors are 1,450/1,833, and semantically owned accepted intervals are 447/1,833.}",
        "\\caption{Selective assurance operating point. Precision, proposal coverage, complete-document automation, and held-out v003 evidence are shown together. Endpoint-field anchors are 3,099/3,666, both-endpoint interval anchors are 1,450/1,833, and semantically owned accepted intervals are 447/1,833; endpoint-field coverage and interval-level coverage use different denominators. The raw point is an unselective proposal baseline, not another selective cohort operating point.}",
    )
    body = body.replace(
        "\\caption{Full-support and matched-support downstream consequences. Full-support and matched-support are distinct estimands; matched-support results use the identical 15 accepted documents.}",
        "\\caption{Full-support and matched-support downstream consequences. Solid bars use each extraction policy's available observations, whereas hatched bars use the identical 15 accepted documents. These are distinct estimands, not a direct value-correction comparison. NN denotes nearest-neighbour distance; grid distance denotes grid-to-nearest-observation distance.}",
    )
    body = body.replace(
        "\\caption{Provenance-grounded assurance framework. VLM proposals are checked against independent positioned evidence and deterministic geometry before acceptance or review.}",
        "\\caption{Provenance-grounded assurance framework. VLM proposals are checked against independent positioned evidence and deterministic geometry before acceptance or review.}\\label{fig:framework}",
    )
    body = body.replace(
        "\\caption{Modern VLM reliability across California cohorts and source shift. The familiar-source panel compares Qwen3.8-27B-FP8 with the positioned RapidOCR parser on five record-disjoint California cohorts with published manual-transcription Gold evidence. The source-shift panel reports Swissgeol, British Geological Survey (BGS), and Raft River transfer/stress outcomes with their declared evidence tiers; these values are not pooled with California Gold.}",
        "\\caption{Modern VLM reliability across California cohorts and source shift. The familiar-source panel compares Qwen3.8-27B-FP8 with the positioned RapidOCR parser on five record-disjoint California cohorts with published manual-transcription Gold evidence. The source-shift panel reports Swissgeol, British Geological Survey (BGS), and Raft River transfer/stress outcomes with their declared evidence tiers; these values are not pooled with California Gold.}\\label{fig:capability}",
    )
    body = body.replace(
        "\\caption{Selective assurance operating point. Precision, proposal coverage, complete-document automation, and held-out v003 evidence are shown together. Endpoint-field anchors are 3,099/3,666, both-endpoint interval anchors are 1,450/1,833, and semantically owned accepted intervals are 447/1,833; endpoint-field coverage and interval-level coverage use different denominators. The raw point is an unselective proposal baseline, not another selective cohort operating point.}",
        "\\caption{Selective assurance operating point. Precision, proposal coverage, complete-document automation, and held-out v003 evidence are shown together. Endpoint-field anchors are 3,099/3,666, both-endpoint interval anchors are 1,450/1,833, and semantically owned accepted intervals are 447/1,833; endpoint-field coverage and interval-level coverage use different denominators. The raw point is an unselective proposal baseline, not another selective cohort operating point.}\\label{fig:assurance}",
    )
    body = body.replace(
        "\\caption{Full-support and matched-support downstream consequences. Solid bars use each extraction policy's available observations, whereas hatched bars use the identical 15 accepted documents. These are distinct estimands, not a direct value-correction comparison. NN denotes nearest-neighbour distance; grid distance denotes grid-to-nearest-observation distance.}",
        "\\caption{Full-support and matched-support downstream consequences. Solid bars use each extraction policy's available observations, whereas hatched bars use the identical 15 accepted documents. These are distinct estimands, not a direct value-correction comparison. NN denotes nearest-neighbour distance; grid distance denotes grid-to-nearest-observation distance.}\\label{fig:spatial}",
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
        credit_roles = (
            "Conceptualization; Data curation; Formal analysis; Investigation; "
            "Methodology; Project administration; Resources; Software; "
            "Validation; Visualization; Writing -- original draft; "
            "Writing -- review and editing"
        )
        final_md = source.replace(
            "# " + TITLE,
            "# " + TITLE + "\n\n**Author:** Yifan Du\\\n**Affiliation:** North China University of Water Resources and Electric Power, Zhengzhou, Henan 450046, China\\\n**Corresponding author:** Yifan Du (duyifan619916@gmail.com)\\\n**ORCID:** 0009-0008-7740-5408\n\n**CRediT author statement:** Conceptualization; Data curation; Formal analysis; Investigation; Methodology; Project administration; Resources; Software; Validation; Visualization; Writing -- original draft; Writing -- review and editing.",
            1,
        )
        final_md = re.sub(
            r"## Computer Code Availability.*?## Data Availability",
            "## Computer Code Availability\n\n" + CODE_AVAILABILITY + "\n\n## Data Availability",
            final_md,
            flags=re.S,
        )
        final_md = re.sub(
            r"## Data Availability.*?## Declarations",
            "## Data Availability\n\n" + DATA_AVAILABILITY + "\n\n## Declarations",
            final_md,
            flags=re.S,
        )
        final_md = re.sub(
            r"## Declarations.*?## References",
            "## Declarations\n\n" + DECLARATIONS + "\n\n## References",
            final_md,
            flags=re.S,
        )
        final_md = re.sub(r"\n\*\*Table 3\.\*\*.*?(?=\n## Computer Code Availability)", "\n", final_md, flags=re.S)
        final_md = final_md.replace(
            "![Figure 2. Modern VLM reliability across California cohorts and source shift.]",
            "![Figure 2. Modern VLM reliability across California cohorts and source shift. The familiar-source panel compares Qwen3.8-27B-FP8 with the positioned RapidOCR parser on five record-disjoint California cohorts with published manual-transcription Gold evidence. The source-shift panel reports Swissgeol, British Geological Survey (BGS), and Raft River transfer/stress outcomes with their declared evidence tiers; these values are not pooled with California Gold.]",
        )
        final_md = final_md.replace(
            "![Figure 3. Selective assurance viewed simultaneously as precision, proposal coverage, complete-document automation, and a held-out v003 evidence funnel. Numeric anchors are reported separately as endpoint-field coverage (3,099/3,666) and as both-endpoint interval coverage (1,450/1,833); only semantically owned intervals are accepted.]",
            "![Figure 3. Selective assurance operating point. Precision, proposal coverage, complete-document automation, and held-out v003 evidence are shown together. Endpoint-field anchors are 3,099/3,666, both-endpoint interval anchors are 1,450/1,833, and semantically owned accepted intervals are 447/1,833; endpoint-field coverage and interval-level coverage use different denominators. The raw point is an unselective proposal baseline, not another selective cohort operating point.]",
        )
        final_md = final_md.replace(
            "![Figure 4. Full-support versus matched-support downstream consequence of selective acceptance.]",
            "![Figure 4. Full-support versus matched-support downstream consequence of selective acceptance. Solid bars use each policy's available observations; hatched bars use the identical 15 accepted documents. These are distinct estimands. NN means nearest-neighbour distance; grid distance means grid-to-nearest-observation distance.]",
        )
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
