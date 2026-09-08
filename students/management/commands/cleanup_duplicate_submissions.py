from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db.models import Count

from students.models import Student


class Command(BaseCommand):
    help = (
        "Removes duplicate students created by re-uploading the same bulk "
        "submissions CSV multiple times. A group is only treated as a true "
        "duplicate (and deleted) when first_name + last_name + school + "
        "grade + idea title ALL match — the oldest record in each group is "
        "kept, the rest (and their login accounts, ideas, team memberships) "
        "are deleted. Run with --dry-run first to preview."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Only report what would be deleted, without deleting anything.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        groups = (
            Student.objects.values('user__first_name', 'user__last_name', 'school__name', 'grade')
            .annotate(cnt=Count('id'))
            .filter(cnt__gt=1)
        )

        to_delete_user_ids = []
        kept_count = 0
        skipped_mixed_groups = 0

        for g in groups:
            students = list(
                Student.objects.filter(
                    user__first_name=g['user__first_name'],
                    user__last_name=g['user__last_name'],
                    school__name=g['school__name'],
                    grade=g['grade'],
                ).select_related('user').order_by('created_at')
            )

            titles = set()
            for s in students:
                idea = s.ideasubmission_set.first()
                titles.add(idea.title if idea else None)

            if len(titles) != 1:
                # Idea titles differ within the group -> likely genuinely
                # different students who happen to share a name; leave alone.
                skipped_mixed_groups += 1
                continue

            kept_count += 1
            for s in students[1:]:
                to_delete_user_ids.append(s.user_id)

        self.stdout.write(f'Duplicate groups found: {groups.count()}')
        self.stdout.write(f'Groups confirmed as true re-upload duplicates: {kept_count}')
        self.stdout.write(f'Groups skipped (idea titles differ, likely different students): {skipped_mixed_groups}')
        self.stdout.write(f'Students to delete: {len(to_delete_user_ids)}')

        if dry_run:
            self.stdout.write(self.style.WARNING('Dry run — nothing deleted.'))
            return

        if not to_delete_user_ids:
            self.stdout.write(self.style.SUCCESS('Nothing to delete.'))
            return

        before_students = Student.objects.count()
        User.objects.filter(id__in=to_delete_user_ids).delete()
        after_students = Student.objects.count()

        self.stdout.write(self.style.SUCCESS(
            f'Deleted {before_students - after_students} duplicate student(s). '
            f'{after_students} student(s) remain.'
        ))
