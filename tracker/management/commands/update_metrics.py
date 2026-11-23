from django.core.management.base import BaseCommand
from tracker.models import OperationalMetric, local_owner

class Command(BaseCommand):
    help = "View or update Operational Metrics in the tracker."

    def add_arguments(self, parser):
        parser.add_argument("--total-batches", type=int, help="Total batches handled")
        parser.add_argument("--batches-completed", type=int, help="Batches completed")
        parser.add_argument("--total-students", type=int, help="Total students")
        parser.add_argument("--students-completed", type=int, help="Students completed")
        parser.add_argument("--project-evals", type=int, help="Project evaluations conducted")
        parser.add_argument("--mock-interviews", type=int, help="Mock interviews conducted")
        parser.add_argument("--support-enquiries", type=int, help="Admissions & support enquiries")
        parser.add_argument("--syllabus-updates", type=int, help="Syllabus updates")
        parser.add_argument("--placements-supported", type=int, help="Placements supported")
        parser.add_argument("--notes", type=str, help="Operational highlights / notes")
        parser.add_argument("--show", action="store_true", help="Print current operational metrics")

    def handle(self, *args, **options):
        metric = OperationalMetric.get_for(local_owner())
        updated = False

        field_mapping = {
            "total_batches": options.get("total_batches"),
            "batches_completed": options.get("batches_completed"),
            "total_students": options.get("total_students"),
            "students_completed": options.get("students_completed"),
            "project_evaluations": options.get("project_evals"),
            "mock_interviews": options.get("mock_interviews"),
            "support_enquiries": options.get("support_enquiries"),
            "syllabus_updates": options.get("syllabus_updates"),
            "placements_supported": options.get("placements_supported"),
        }

        for field, val in field_mapping.items():
            if val is not None:
                setattr(metric, field, max(0, val))
                updated = True

        if options.get("notes") is not None:
            metric.notes = options.get("notes").strip()
            updated = True

        if updated:
            metric.save()
            self.stdout.write(self.style.SUCCESS("Operational metrics updated successfully."))

        self.stdout.write("Current Operational Metrics:")
        for k, v in metric.to_dict().items():
            self.stdout.write(f"  {k}: {v}")
