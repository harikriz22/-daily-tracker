import datetime
from django.core.management.base import BaseCommand, CommandError
from tracker.models import Record, OperationalMetric, local_owner

class Command(BaseCommand):
    help = "Add a new task, progress, or evaluation record to the Daily Progress & Performance Tracker."

    def add_arguments(self, parser):
        parser.add_argument("title", type=str, nargs="?", help="Title or summary of the task/record")
        parser.add_argument(
            "-c", "--category",
            type=str,
            default="Task",
            choices=[c[0] for c in Record.CATEGORY_CHOICES],
            help="Category (e.g. Task, Learning, Batch, ProjectEval, MockInterview, Achievement, etc.)"
        )
        parser.add_argument(
            "-d", "--date",
            type=str,
            default=None,
            help="Date in YYYY-MM-DD format (defaults to today)"
        )
        parser.add_argument(
            "-n", "--notes",
            type=str,
            default="",
            help="Additional details or notes about the record"
        )
        parser.add_argument(
            "-H", "--hours",
            type=float,
            default=None,
            help="Hours spent on the task/activity"
        )
        parser.add_argument(
            "--no-metric-sync",
            action="store_true",
            help="Do not automatically increment related operational metrics"
        )

    def handle(self, *args, **options):
        title = options.get("title")
        if not title:
            raise CommandError("Please provide a title for the record.")

        date_str = options.get("date")
        if date_str:
            try:
                record_date = datetime.date.fromisoformat(date_str)
            except ValueError:
                raise CommandError(f"Invalid date format '{date_str}'. Expected YYYY-MM-DD.")
        else:
            record_date = datetime.date.today()

        category = options.get("category")
        notes = options.get("notes") or ""
        hours = options.get("hours")

        owner = local_owner()
        record = Record.objects.create(
            user=owner,
            date=record_date,
            category=category,
            title=title.strip(),
            notes=notes.strip(),
            hours=round(hours, 2) if hours is not None else None
        )

        metric_updated = False
        if not options.get("no_metric_sync"):
            metric_updated = OperationalMetric.bump(owner, category, +1)

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully added record [{record.id}]: '{record.title}' on {record.date} (Category: {record.category})"
            )
        )
        if metric_updated:
            self.stdout.write(self.style.SUCCESS(f"Updated associated Operational Metric for category '{category}'."))
