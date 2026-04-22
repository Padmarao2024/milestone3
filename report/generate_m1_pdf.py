#!/usr/bin/env python3
"""Generate Milestone 1 report PDF (<=3 pages) with architecture diagram."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

REPO = "https://github.com/Padmarao2024/milestone3"
ACTIONS = "https://github.com/Padmarao2024/milestone3/actions"
DOCKER = "https://hub.docker.com/r/padmarao369/recommender-api/tags"
CLOUD = "https://recommender-api.gentlemushroom-c3c537f6.eastus.azurecontainerapps.io/health"
PROJECT_BOARD = "https://github.com/users/Padmarao2024/projects"

REPORT_DIR = Path(__file__).parent
SCREEN_DIR = REPORT_DIR / "screenshots"
SCREEN_DIR.mkdir(parents=True, exist_ok=True)
OUT_PDF = REPORT_DIR / "PadmaraoPulicharla_M1_Report.pdf"
DIAGRAM = SCREEN_DIR / "m1_architecture.png"
TEAM_MEMBER = "Padmarao Pulicharla"


def make_diagram() -> None:
    fig, ax = plt.subplots(figsize=(10, 5.8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")

    def box(x, y, w, h, label, fc="#eaf2ff"):
        rect = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                              linewidth=1.2, edgecolor="#1f3b6f", facecolor=fc)
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=9)

    box(0.5, 4.2, 1.8, 1.1, "Probe\nProducer")
    box(3.0, 4.2, 2.0, 1.1, "Kafka Topics\nwatch/rate/reco")
    box(5.7, 4.2, 1.8, 1.1, "Ingestor\n+ Validator")
    box(8.0, 4.2, 1.5, 1.1, "Snapshots\nParquet")

    box(0.8, 2.2, 2.0, 1.1, "Training Jobs\n(ALS/item/pop)")
    box(3.3, 2.2, 2.0, 1.1, "Model Registry\nversion+metadata")
    box(5.8, 2.2, 1.9, 1.1, "API Service\n/recommend /metrics")
    box(8.1, 2.2, 1.4, 1.1, "Clients")

    box(1.8, 0.5, 2.2, 1.1, "GitHub Actions\ntest-build-push-deploy")
    box(4.6, 0.5, 2.0, 1.1, "Container Registry\nDocker Hub")
    box(7.2, 0.5, 2.0, 1.1, "Azure Container Apps\n+ Monitoring")

    def arrow(x1, y1, x2, y2):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", lw=1.2, color="#2a4d8f"))

    arrow(2.3, 4.75, 3.0, 4.75)
    arrow(5.0, 4.75, 5.7, 4.75)
    arrow(7.5, 4.75, 8.0, 4.75)
    arrow(8.8, 4.2, 7.0, 3.3)
    arrow(8.0, 2.75, 8.1, 2.75)

    arrow(2.8, 2.75, 3.3, 2.75)
    arrow(5.3, 2.75, 5.8, 2.75)

    arrow(3.0, 1.6, 4.6, 1.1)
    arrow(6.6, 1.1, 7.2, 1.1)
    arrow(8.2, 1.6, 6.8, 2.2)

    ax.text(0.4, 5.7, "Milestone 1 Architecture Proposal", fontsize=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(DIAGRAM, dpi=180, bbox_inches="tight")
    plt.close(fig)


def tbl(data, widths):
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3b6f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef3ff")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    return t


def build_pdf() -> None:
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Heading1"], fontSize=13, spaceAfter=4)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=10, spaceBefore=4, spaceAfter=2)
    body = ParagraphStyle("body", parent=styles["Normal"], fontSize=8.4, leading=10, spaceAfter=2)
    small = ParagraphStyle("small", parent=styles["Normal"], fontSize=7.8, leading=9, spaceAfter=2)
    hr = HRFlowable(width="100%", thickness=0.5, color=colors.grey, spaceAfter=4)

    doc = SimpleDocTemplate(
        str(OUT_PDF),
        pagesize=letter,
        leftMargin=0.70 * inch,
        rightMargin=0.70 * inch,
        topMargin=0.58 * inch,
        bottomMargin=0.58 * inch,
    )

    story = [
        Paragraph("Padmarao Pulicharla - Milestone 1: Team Contract and Technical Proposal", h1),
        Paragraph(f"Repo: <link href='{REPO}'>{REPO}</link>", small),
        Paragraph(f"Actions: <link href='{ACTIONS}'>{ACTIONS}</link> | Registry: <link href='{DOCKER}'>{DOCKER}</link> | Cloud URL: <link href='{CLOUD}'>{CLOUD}</link>", small),
        hr,
        Paragraph("1) Team Contract", h2),
        Paragraph("Team members and skills", body),
        tbl([
            ["Member", "Bio", "Skills"],
            [TEAM_MEMBER, "Solo project owner building production-style recommender pipelines", "Python, FastAPI, Kafka, Azure, CI/CD, MLOps"],
        ], [1.5 * inch, 2.4 * inch, 2.3 * inch]),
        Spacer(1, 4),
        Paragraph("Roles and backups", body),
        tbl([
            ["Role", "Primary", "Backup"],
            ["PM / Technical Lead", TEAM_MEMBER, TEAM_MEMBER],
            ["ML Lead", TEAM_MEMBER, TEAM_MEMBER],
            ["Data/Streaming Lead", TEAM_MEMBER, TEAM_MEMBER],
            ["DevOps/Cloud Lead", TEAM_MEMBER, TEAM_MEMBER],
        ], [2.2 * inch, 1.8 * inch, 1.8 * inch]),
        Spacer(1, 4),
        Paragraph("Communication, cadence, expectations, and decisions", body),
        tbl([
            ["Section", "Agreement"],
            ["Communication", "Slack/Teams channel; response SLA <= 12h weekdays; escalation via direct call for outages."],
            ["Cadence", "Weekly standup Sunday 7:00 PM IST; 1-week sprint; milestone demo dry-run 24h before deadline."],
            ["Definition of Done", "PR review checklist, passing tests/lint, updated docs, reproducible script output."],
            ["Decision process", "Model changes by metric review; rollback on SLO breach or error-rate alert >5%."],
            ["Risk and contingency", "Cloud quota monitoring, backup local runs, fallback popularity model, on-call during probe windows."],
            ["Peer accountability", "Self/peer score 1-5 each milestone with notes and corrective action if <3."],
        ], [1.55 * inch, 4.25 * inch]),
        PageBreak(),
        Paragraph("2) Technical Proposal", h2),
        Paragraph("Problem framing and API contract", body),
        tbl([
            ["Endpoint", "Contract", "SLO target"],
            ["GET /health", "Liveness check with model version", "99% availability over assignment window"],
            ["GET /recommend?user_id=&k=", "Return ranked items, model, provenance fields", "p95 latency <= 500 ms, error rate <= 5%"],
            ["GET /metrics", "Prometheus metrics", "Scrape every 30s"],
        ], [1.7 * inch, 2.8 * inch, 1.3 * inch]),
        Spacer(1, 4),
        Paragraph("Architecture diagram and rationale", body),
        Image(str(DIAGRAM), width=6.1 * inch, height=3.5 * inch),
        Spacer(1, 4),
        Paragraph("Cloud and tooling choices: FastAPI + Uvicorn runtime, Docker Hub registry, Azure Container Apps deployment, Kafka topics for streaming, Parquet snapshot storage, GitHub Actions for CI/CD, and Prometheus-compatible metrics.", small),
        Paragraph("Data plan: MovieLens snapshot baseline plus event replay via watch/rate topics; snapshots versioned by date and environment; schema-validated ingestion.", small),
        Paragraph("MLOps plan: tests -> build -> push -> deploy pipeline; semantic model version metadata (version, git_sha, snapshot_id, trained_at, image_digest); reproducible training scripts.", small),
        Paragraph("Milestone Gantt with owners", body),
        tbl([
            ["Milestone", "Owner", "Window", "Output"],
            ["M1", TEAM_MEMBER, "Week 1", "Contract + architecture + repo skeleton"],
            ["M2", TEAM_MEMBER, "Week 2", "Data ingestion + baseline models + eval"],
            ["M3", TEAM_MEMBER, "Week 3", "CI/CD + cloud deployment + evidence"],
            ["M4", TEAM_MEMBER, "Week 4", "Monitoring + retrain + A/B + provenance"],
            ["M5", TEAM_MEMBER, "Week 5", "Responsible ML analysis + reflection"],
        ], [0.8 * inch, 1.3 * inch, 1.1 * inch, 3.0 * inch]),
        PageBreak(),
        Paragraph("3) Risks, Repo Hygiene, and CI/CD Minimum", h2),
        Paragraph("Top-5 risk register", body),
        tbl([
            ["Risk", "Impact", "Mitigation"],
            ["Cloud quota exhaustion", "Deploy failure", "Use one ACA env, clean stale resources, keep local fallback runs"],
            ["Kafka auth/secrets leak", "Security incident", "GitHub Secrets + rotation policy + never commit keys"],
            ["Schema drift across producers", "Pipeline break", "Pandera validation + strict event contracts + tests"],
            ["Model quality regressions", "Poor recommendations", "A/B gate, benchmark thresholds, rollback via /switch"],
            ["CI/CD breakages", "Delivery delay", "Pinned deps, test gates, deployment summary in Action output"],
        ], [1.6 * inch, 1.3 * inch, 2.9 * inch]),
        Spacer(1, 4),
        Paragraph("Repo hygiene and governance", body),
        tbl([
            ["Item", "Status / Link"],
            ["Repository", f"{REPO}"],
            ["README and structure", "Present with module boundaries and run instructions"],
            ["Issue labels", "Planned labels: bug, enhancement, ml, data, infra, docs"],
            ["Project board", f"{PROJECT_BOARD}"],
        ], [1.5 * inch, 4.3 * inch]),
        Spacer(1, 4),
        Paragraph("CI/CD and secrets minimum", body),
        Paragraph("Workflow enforces tests -> image build -> push -> deploy. Secrets are managed in GitHub Environments/Secrets: Kafka bootstrap/API creds, Schema Registry URL, Docker Hub token, Azure deploy credentials, and app/resource settings. Deployment status writes URL and image source/digest information to GitHub Action Summary.", body),
        Paragraph("Submission links summary: GitHub repo, Actions runs, registry images, cloud URL, and Kafka console screenshot/read-only link can be attached in report/screenshots/.", small),
    ]

    doc.build(story)


def main() -> None:
    make_diagram()
    build_pdf()
    print(f"Generated {DIAGRAM}")
    print(f"Generated {OUT_PDF}")


if __name__ == "__main__":
    main()
