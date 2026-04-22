#!/usr/bin/env python3
"""Generate Milestone 5 report PDF (<=6 pages; demo section intentionally omitted)."""

from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

REPO = "https://github.com/Padmarao2024/milestone3"
REPORT_DIR = Path(__file__).parent
SUMMARY_JSON = REPORT_DIR / "m5_summary.json"

styles = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=13, spaceAfter=4)
H2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=10, spaceAfter=2, spaceBefore=6)
BODY = ParagraphStyle("Body", parent=styles["Normal"], fontSize=8.5, spaceAfter=2, leading=10)
SMALL = ParagraphStyle("Small", parent=styles["Normal"], fontSize=8, spaceAfter=2, leading=9)
CODE = ParagraphStyle("Code", parent=styles["Code"], fontSize=7.3, spaceAfter=2, backColor=colors.whitesmoke)
HR = HRFlowable(width="100%", thickness=0.5, color=colors.grey, spaceAfter=4)


def sp(h: int = 6) -> Spacer:
    return Spacer(1, h)


def tbl(data, widths):
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3b6f")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#edf2fb")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    return t


def add_img(path: Path, width: float = 6.1 * inch, max_h: float = 2.5 * inch):
    if not path.exists():
        return [Paragraph(f"[missing image: {path.name}]", CODE)]
    from PIL import Image as PILImage

    with PILImage.open(path) as im:
        w, h = im.size
    aspect = h / w
    h_out = min(width * aspect, max_h)
    w_out = h_out / aspect
    return [Image(str(path), width=w_out, height=h_out)]


def build() -> None:
    if not SUMMARY_JSON.exists():
        raise FileNotFoundError("Run report/generate_m5_assets.py first")

    summary = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))

    fairness_csv = REPORT_DIR / "m5_fairness_summary.csv"
    loop_sec_csv = REPORT_DIR / "m5_loop_security_summary.csv"

    out = REPORT_DIR / "milestone5_submission.pdf"
    doc = SimpleDocTemplate(
        str(out),
        pagesize=letter,
        leftMargin=0.72 * inch,
        rightMargin=0.72 * inch,
        topMargin=0.60 * inch,
        bottomMargin=0.58 * inch,
    )

    fs = summary["fairness"]
    lp = summary["loop_analysis"]
    sec = summary["security_analysis"]

    story = [
        Paragraph("Milestone 5 - Responsible ML Analysis and Reflection", H1),
        Paragraph("Repository: <link href='%s'>%s</link>" % (REPO, REPO), SMALL),
        Paragraph("Scope note: Demo/video section intentionally excluded per current request.", SMALL),
        HR,
        Paragraph("1. Fairness Requirements", H2),
        Paragraph(
            "Potential harms in this recommender include: (a) popularity bias that over-exposes already "
            "frequent items, (b) poor quality for low-history users (cold/warm groups), and (c) proxy bias where "
            "interaction volume acts as a proxy for user value. We define one system-level and one model-level "
            "requirement with measurable thresholds.",
            BODY,
        ),
        tbl(
            [
                ["Requirement", "Metric", "Threshold", "Current", "Status"],
                [
                    "System-level fairness",
                    "personalized_rate (telemetry)",
                    ">= 0.40",
                    f"{fs['system_personalized_rate']['value']:.4f}",
                    "PASS" if fs["system_personalized_rate"]["pass"] else "FAIL",
                ],
                [
                    "Model-level fairness",
                    "warm-hot NDCG gap (item_item)",
                    "<= 0.30",
                    f"{fs['model_warm_hot_ndcg_gap_item_item']['value']:.4f}",
                    "PASS" if fs["model_warm_hot_ndcg_gap_item_item"]["pass"] else "FAIL",
                ],
            ],
            [1.7 * inch, 1.7 * inch, 1.0 * inch, 0.9 * inch, 0.7 * inch],
        ),
        sp(6),
        Paragraph("2. Fairness Improvements (Collection, Design, Monitoring)", H2),
        Paragraph(
            "Collection actions: increase tail-item and cold-user probe coverage; record per-response item IDs in "
            "telemetry to compute direct exposure parity. Design actions: add diversity-aware reranking with an "
            "exposure cap on top-10 most shown items per hour; enforce a minimum share of recommendations from "
            "long-tail items. Monitoring actions: schedule fairness checks from report/m5_fairness_summary.csv and "
            "raise alerts when warm-hot NDCG gap exceeds threshold for two consecutive windows.",
            BODY,
        ),
        sp(4),
        Paragraph("3. Fairness Analysis (Telemetry-driven)", H2),
        Paragraph(
            "Telemetry from report/online_kpi_summary.csv gives personalized_rate=%.4f. This satisfies the system-level "
            "requirement (>=0.40), so fairness support at system level is currently acceptable. However, subpopulation "
            "analysis from report/offline_subpopulations.csv shows a large warm-hot quality gap in item_item, indicating "
            "remaining inequity for heavy-history users versus warm users."
            % fs["system_personalized_rate"]["value"],
            BODY,
        ),
        *add_img(REPORT_DIR / "screenshots" / "m5_fairness.png"),
        sp(4),
        Paragraph("Evidence files: report/m5_fairness_summary.csv, report/online_kpi_summary.csv, report/offline_subpopulations.csv", SMALL),
        HR,
        Paragraph("4. Feedback Loops", H2),
        Paragraph(
            "Loop A (Popularity Echo): popular items get more exposure, which increases future interactions and "
            "further increases exposure. Detection idea: monitor item distribution TVD and top-k item share over time. "
            "Loop B (Tail Starvation): low-frequency items receive little exposure, reducing chance of future feedback. "
            "Detection idea: monitor long-tail exposure ratio and decay in unique_items over windows.",
            BODY,
        ),
        Paragraph("5. Loop Analysis using Telemetry", H2),
        Paragraph(
            "Using report/drift_report.csv, item_distribution_tvd=%.4f against threshold %.4f. Result: %s. "
            "This is evidence of loop pressure (distribution shift consistent with popularity-echo behavior), though the "
            "dataset is small and should be re-validated on a longer observation window."
            % (
                lp["item_distribution_tvd"],
                lp["threshold"],
                "DETECTED" if lp["detected"] else "NO DETECTION",
            ),
            BODY,
        ),
        *add_img(REPORT_DIR / "screenshots" / "m5_loop_security.png"),
        sp(4),
        Paragraph("Evidence files: report/m5_loop_security_summary.csv, report/drift_report.csv", SMALL),
        HR,
        Paragraph("6. Security Threat Model and Mitigations", H2),
        tbl(
            [
                ["Surface", "Threat", "Mitigation"],
                [
                    "Kafka ingress (watch/rate)",
                    "Rating spam / poisoning",
                    "Schema validation in pipeline.quality + ingestor.validator; anomaly checks on user contribution share",
                ],
                [
                    "API /recommend",
                    "Abuse & resource exhaustion",
                    "Input bounds on k, exception accounting, latency/error metrics, operational alert runbook",
                ],
                [
                    "Model registry",
                    "Unauthorized model update",
                    "GitHub Actions permission scoping, commit provenance (git sha), environment-based version pinning",
                ],
            ],
            [1.25 * inch, 1.55 * inch, 3.3 * inch],
        ),
        sp(4),
        Paragraph(
            "Model-attack focus: poisoning via coordinated high-volume ratings from a small set of user_ids. "
            "Operational mitigations include rate limiting and auth at API gateway (planned), schema checks (implemented), "
            "and deployment approvals for retrain promotion (implemented via workflow controls).",
            BODY,
        ),
        Paragraph("7. Security Analysis using Telemetry", H2),
        Paragraph(
            "We ran a telemetry detection on interactions.parquet: max user contribution share=%.4f with threshold %.2f. "
            "Suspicious users above threshold: %d. Result: %s. This is a null finding for rating-spam in the current window."
            % (
                sec["max_user_share"],
                sec["threshold"],
                int(sec["suspicious_users"]),
                "DETECTED" if sec["detected"] else "NO DETECTION",
            ),
            BODY,
        ),
        Paragraph("Evidence files: report/m5_loop_security_summary.csv, data/processed/interactions.parquet", SMALL),
        HR,
        PageBreak(),
        Paragraph("8. Reflection", H2),
        Paragraph(
            "This section summarizes technical and teamwork lessons across Milestones 3-5. The objective is to identify "
            "what was genuinely hard in production-like operation, where the current system is fragile, and how the team "
            "would redesign the implementation for a cleaner V2.",
            BODY,
        ),
        Paragraph("8.1 Hardest technical areas", H2),
        Paragraph(
            "The most difficult issue was offset correctness when moving from local testing to repeatable Kafka ingestion. "
            "At low volumes, replaying from earliest offset looked harmless, but under repeated runs it created hidden "
            "duplication and made KPI windows unstable. A second challenge was schema evolution: adding fields for provenance "
            "and experimentation required synchronizing producer, validator, and consumer expectations. The third challenge "
            "was cold starts and model fallback behavior; popularity fallback protects uptime but can mask quality problems in "
            "personalized models if telemetry is not segmented carefully.",
            BODY,
        ),
        Paragraph("8.2 Current fragilities", H2),
        Paragraph(
            "The current telemetry lacks per-item exposure logs in online responses, which limits direct fairness auditing "
            "of long-tail coverage. Security detection is also limited by small windows and basic heuristics (for example, "
            "user contribution concentration). Alerting currently combines implemented checks with a runbook, but not all "
            "mitigations are enforced automatically at gateway level. Finally, report evidence quality depends on short "
            "evaluation windows, making some findings directional rather than statistically robust.",
            BODY,
        ),
        Paragraph("8.3 Productionization plan", H2),
        Paragraph(
            "If this were promoted to production, the first upgrades would be: (1) API gateway auth + strict per-client "
            "rate limits; (2) persistent recommendation event schema that stores served item IDs, score, and rank for every "
            "request; (3) scheduled fairness and security jobs that fail CI if thresholds are violated; (4) canary retrain "
            "promotion with explicit approvals and rollback; and (5) longer-horizon observability dashboards with 7-day and "
            "30-day cohorts to reduce noise in decisions.",
            BODY,
        ),
        Paragraph("8.4 If we redid it", H2),
        Paragraph(
            "The redesign would start with data contracts first, not model code first. We would define telemetry and "
            "provenance schemas before implementing endpoint behavior, then build training and serving around those contracts. "
            "We would also separate experimentation traffic from baseline traffic at ingestion time to make attribution easier. "
            "On the team side, earlier role ownership (ingestion lead, API lead, evaluation lead, ops lead) would reduce "
            "integration churn and minimize late-stage firefighting.",
            BODY,
        ),
    ]

    doc.build(story)
    print(f"Wrote {out}")


if __name__ == "__main__":
    build()
