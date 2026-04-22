from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "report" / "milestone3_submission_4pages.pdf"


def link(path: str) -> str:
    return f"<font name='Courier'>{path}</font>"


def bullet_lines(items, style):
    lines = []
    for item in items:
        lines.append(Paragraph(f"&bull; {item}", style))
        lines.append(Spacer(1, 0.05 * inch))
    return lines


def make_table(rows, col_widths):
    table = Table(rows, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#153B50")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#8AA1B1")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.HexColor("#F5F7FA")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def screenshot_box(title: str, note: str, width: float = 6.8 * inch, height: float = 1.25 * inch):
    table = Table(
        [[Paragraph(f"<b>{title}</b><br/>{note}", styles["Small"])]] ,
        colWidths=[width],
        rowHeights=[height],
    )
    table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1.0, colors.HexColor("#6B7C93")),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FAFBFC")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    return table


def page_header(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica-Bold", 9)
    canvas.setFillColor(colors.HexColor("#153B50"))
    canvas.drawString(doc.leftMargin, letter[1] - 0.45 * inch, "Milestone 3 Submission Summary")
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.black)
    canvas.drawRightString(letter[0] - doc.rightMargin, 0.42 * inch, f"Page {doc.page}")
    canvas.restoreState()


styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        name="TitleCenter",
        parent=styles["Title"],
        alignment=TA_CENTER,
        textColor=colors.HexColor("#153B50"),
        fontSize=18,
        leading=22,
        spaceAfter=8,
    )
)
styles.add(
    ParagraphStyle(
        name="Section",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#153B50"),
        fontSize=12,
        leading=14,
        spaceBefore=3,
        spaceAfter=4,
    )
)
styles.add(
    ParagraphStyle(
        name="BodySmall",
        parent=styles["BodyText"],
        fontSize=8.4,
        leading=10.2,
        spaceAfter=3,
    )
)
styles.add(
    ParagraphStyle(
        name="Small",
        parent=styles["BodyText"],
        fontSize=8,
        leading=9.6,
    )
)


def build_story():
    repo_url = "https://github.com/Padmarao2024/milestone3"
    run_url = "https://github.com/Padmarao2024/milestone3/actions/runs/24795929105"
    health_url = "https://recommender-api.gentlemushroom-c3c537f6.eastus.azurecontainerapps.io/health"

    story = []

    story.append(Paragraph("Milestone 3 Recommender System Deliverables", styles["TitleCenter"]))
    story.append(
        Paragraph(
            f"<b>Repository:</b> <a href='{repo_url}' color='blue'>{repo_url}</a><br/>"
            f"<b>Successful CI/CD Run:</b> <a href='{run_url}' color='blue'>{run_url}</a><br/>"
            f"<b>Live Health Endpoint:</b> <a href='{health_url}' color='blue'>{health_url}</a>",
            styles["BodySmall"],
        )
    )
    story.append(Spacer(1, 0.06 * inch))

    story.append(Paragraph("1. Pipeline Structure & Config Separation", styles["Section"]))
    story.extend(
        bullet_lines(
            [
                f"Shared package layout cleanly separates config, quality, transform, train, serve, and eval in {link('pipeline/') }.",
                f"Environment-based configuration is centralized in {link('pipeline/config.py')} instead of being duplicated across scripts.",
                f"Thin operational entrypoints remain in {link('ingestor/')}, {link('training/')}, and {link('api/app/recommender.py')}.",
                "Flow is explicit and reproducible: ingest -> transform -> train -> serialize -> serve -> eval.",
            ],
            styles["BodySmall"],
        )
    )
    story.append(
        Paragraph(
            "Primary code links: "
            f"{link('pipeline/config.py')}, {link('pipeline/quality.py')}, {link('pipeline/transform.py')}, "
            f"{link('pipeline/train.py')}, {link('pipeline/serve.py')}, {link('pipeline/eval.py')}",
            styles["BodySmall"],
        )
    )

    story.append(Paragraph("2. Offline Evaluation Spec & Reproducibility", styles["Section"]))
    story.extend(
        bullet_lines(
            [
                "Split: per-user chronological leave-last holdout to preserve temporal ordering.",
                "Leakage control: recommendation history uses only pre-holdout interactions per user.",
                "Metrics: HR@10 and NDCG@10, plus subpopulation analysis and benchmark support metrics.",
                f"Reproducible entrypoints and artifacts: {link('training/evaluate.py')}, {link('report/offline_metrics.csv')}, {link('report/offline_subpopulations.csv')}, {link('report/benchmark.csv')}."
            ],
            styles["BodySmall"],
        )
    )

    story.append(
        make_table(
            [
                ["Model", "HR@10", "NDCG@10", "Users"],
                ["als", "0.3333", "0.1667", "3"],
                ["item_item", "0.3333", "0.2103", "3"],
                ["popularity", "0.3333", "0.1667", "3"],
            ],
            [1.7 * inch, 1.0 * inch, 1.1 * inch, 0.8 * inch],
        )
    )
    story.append(Spacer(1, 0.08 * inch))
    story.append(
        Paragraph(
            "Subpopulation highlight: item-item reaches HR@10 = 1.0 and NDCG@10 = 0.6309 on warm users; all models are weak on the hot bucket in this small sample.",
            styles["BodySmall"],
        )
    )

    story.append(PageBreak())

    story.append(Paragraph("3. Online KPI from Kafka Logs", styles["Section"]))
    story.extend(
        bullet_lines(
            [
                "Source topic: alpha.reco_responses.",
                "Proxy success definition: status_code == 200, num_results >= 1, and latency_ms <= 2000.",
                "Supporting KPIs: healthy_response_rate, personalized_rate, error_rate, latency_ms_p95.",
                f"Implementation and outputs: {link('pipeline/eval.py')}, {link('training/online_eval.py')}, {link('report/online_kpi_summary.csv')}, {link('report/online_kpi_by_model.csv')}."
            ],
            styles["BodySmall"],
        )
    )

    story.append(
        make_table(
            [
                ["Responses", "Proxy Success", "Healthy", "Personalized", "P95 Latency", "Error"],
                ["6", "83.33%", "83.33%", "50.00%", "15381 ms", "16.67%"],
            ],
            [0.8 * inch, 1.1 * inch, 0.9 * inch, 1.0 * inch, 1.0 * inch, 0.8 * inch],
        )
    )
    story.append(Spacer(1, 0.08 * inch))
    story.append(
        make_table(
            [
                ["Model", "Responses", "Proxy Success Rate", "Personalized Rate"],
                ["error", "1", "0.00", "0.00"],
                ["item_item", "3", "1.00", "1.00"],
                ["popularity", "2", "1.00", "0.00"],
            ],
            [1.5 * inch, 1.0 * inch, 1.6 * inch, 1.5 * inch],
        )
    )

    story.append(Paragraph("4. Data Quality, Drift, and Backpressure", styles["Section"]))
    story.extend(
        bullet_lines(
            [
                f"Schemas implemented with Pandera in {link('pipeline/quality.py')} and enforced in {link('ingestor/validator.py')}.",
                "Validated payload families: watch, rate, and recommendation response events.",
                f"Backpressure handling is implemented through BackpressureBuffer in {link('pipeline/quality.py')} and used by {link('ingestor/consumer.py')}.",
                f"Drift output is captured in {link('report/drift_report.csv')} as a compact evidence table."
            ],
            styles["BodySmall"],
        )
    )

    story.append(
        make_table(
            [
                ["Drift Check", "Statistic", "Threshold", "Drift"],
                ["item_distribution_tvd", "0.4464", "0.20", "True"],
                ["user_activity_tvd", "0.6667", "0.20", "True"],
                ["unique_users_delta_pct", "0.5000", "0.20", "True"],
                ["unique_items_delta_pct", "0.3333", "0.20", "True"],
            ],
            [2.8 * inch, 1.0 * inch, 1.0 * inch, 0.8 * inch],
        )
    )
    story.append(Spacer(1, 0.08 * inch))
    story.append(
        screenshot_box(
            "Screenshot Placeholder: Drift Evidence",
            "Optional: insert one screenshot of the drift table/chart here before submission if the instructor prefers visual evidence.",
        )
    )

    story.append(PageBreak())

    story.append(Paragraph("5. CI/CD, Deployment, and Test Report", styles["Section"]))
    story.extend(
        bullet_lines(
            [
                f"Workflow files: {link('.github/workflows/ci-cd.yml')} and {link('.github/workflows/probe.yml')}.",
                "Latest successful run contains green jobs for test-and-quality, build-and-push, and deploy-azure-container-apps.",
                "Secrets strategy: DOCKERHUB_USERNAME, DOCKERHUB_TOKEN, AZURE_CREDENTIALS, AZURE_CONTAINER_APP_NAME, AZURE_RESOURCE_GROUP.",
                f"Deployment target is Azure Container Apps; current app health is HTTP 200 at the linked health endpoint.",
                f"Test summary from {link('report/test_report.txt')}: 10 passed, 74.68% coverage on scoped glue modules."
            ],
            styles["BodySmall"],
        )
    )

    story.append(
        make_table(
            [
                ["Requirement", "Status", "Evidence"],
                ["CI checks", "PASS", "Lint + pytest coverage gate green"],
                ["Docker build/push", "PASS", "Docker Hub image built from main"],
                ["Azure deploy", "PASS", "Container App running and healthy"],
                ["Repo hygiene", "PASS", "README, workflows, report artifacts present"],
            ],
            [1.7 * inch, 0.8 * inch, 4.0 * inch],
        )
    )
    story.append(Spacer(1, 0.12 * inch))
    story.append(
        screenshot_box(
            "Screenshot Placeholder: GitHub Actions Success",
            "Add a screenshot of the successful GitHub Actions run page here if you want visual proof in the PDF.",
            height=1.05 * inch,
        )
    )
    story.append(Spacer(1, 0.08 * inch))
    story.append(
        screenshot_box(
            "Screenshot Placeholder: Docker Hub Evidence",
            "Optional: add a screenshot of the recommender-api tags page or successful push evidence from Docker Hub here.",
            height=1.0 * inch,
        )
    )
    story.append(Spacer(1, 0.08 * inch))
    story.append(
        screenshot_box(
            "Screenshot Placeholder: Azure Container App Evidence",
            "Optional: add a screenshot of the Azure Container App overview or health endpoint response here.",
            height=1.0 * inch,
        )
    )

    story.append(PageBreak())

    story.append(Paragraph("6. Deliverables Mapping to Rubric", styles["Section"]))
    story.append(
        Paragraph(
            "This final page maps the requested deliverables directly to the rubric so the submission remains easy to grade within the 4-page limit.",
            styles["BodySmall"],
        )
    )
    story.append(Spacer(1, 0.04 * inch))
    story.append(
        make_table(
            [
                ["Rubric Item", "Coverage in Submission"],
                ["Pipeline clarity & config separation (20)", "Page 1 plus README and pipeline package links."],
                ["Offline eval spec/results/reproducibility (15)", "Page 1 with methodology, metrics table, and artifact links."],
                ["Online KPI from Kafka logs (25)", "Page 2 with methodology and KPI tables from alpha.reco_responses."],
                ["Quality gates (20)", "Page 2 drift table, schemas, tests, and backpressure notes."],
                ["CI/CD builds/pushes/deploys (20)", "Page 3 workflow summary and successful run URL."],
                ["Documentation & repo hygiene (10)", "Pages 1 and 3 with README, report artifacts, and clean module boundaries."],
            ],
            [2.75 * inch, 4.0 * inch],
        )
    )
    story.append(Spacer(1, 0.12 * inch))
    story.append(Paragraph("Code and Evidence Links", styles["Section"]))
    story.extend(
        bullet_lines(
            [
                f"Offline code: {link('pipeline/eval.py')}, {link('training/evaluate.py')}",
                f"Online KPI code: {link('training/online_eval.py')}, {link('report/online_kpi_summary.csv')}",
                f"Quality gates: {link('pipeline/quality.py')}, {link('ingestor/validator.py')}, {link('ingestor/consumer.py')}",
                f"CI/CD and evidence: {link('.github/workflows/ci-cd.yml')}, {link('report/milestone3_evidence.md')}, {link('report/test_report.txt')}",
                f"Live deployment proof: <a href='{health_url}' color='blue'>{health_url}</a>",
            ],
            styles["BodySmall"],
        )
    )
    story.append(Spacer(1, 0.08 * inch))
    story.append(
        Paragraph(
            "If you decide to add screenshots before submission, replace the placeholders on Page 3 with GitHub Actions, Docker Hub, and Azure Portal images. If screenshots are not required, the PDF is already complete as a compact evidence summary.",
            styles["BodySmall"],
        )
    )

    return story


def main():
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=letter,
        leftMargin=0.55 * inch,
        rightMargin=0.55 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.55 * inch,
        title="Milestone 3 Submission Summary",
        author="Padmarao2024",
    )
    doc.build(build_story(), onFirstPage=page_header, onLaterPages=page_header)
    print(OUTPUT)


if __name__ == "__main__":
    main()