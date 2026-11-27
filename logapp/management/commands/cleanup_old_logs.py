"""
예약 로그 자동 정리 Django Management Command
90일(3개월) 이상 된 오래된 로그를 자동으로 삭제하여 데이터베이스 용량을 관리합니다.
"""
import logging
from django.core.management.base import BaseCommand, CommandError
from logapp.cleanup import DEFAULT_RETENTION_DAYS, cleanup_old_booking_logs, retention_cutoff
from logapp.models import BookingLog


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '90일(3개월) 이상 된 예약 로그를 삭제하여 데이터베이스 용량을 관리합니다.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=DEFAULT_RETENTION_DAYS,
            help=f'보관할 일수 (기본: {DEFAULT_RETENTION_DAYS}일, 이보다 오래된 로그 삭제)'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='한 번에 삭제할 로그 수 (기본: 1000개, 메모리 효율성을 위함)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='실제 삭제 없이 시뮬레이션만 실행'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='확인 프롬프트 없이 강제 실행 (cron 등 자동화용)'
        )

    def handle(self, *args, **options):
        days = options['days']
        batch_size = options['batch_size']
        dry_run = options['dry_run']
        force = options['force']

        cutoff_dt = retention_cutoff(days=days)
        cutoff_date = cutoff_dt.date()

        self.stdout.write(
            self.style.SUCCESS(
                f"{'[DRY RUN] ' if dry_run else ''}예약 로그 정리 시작"
            )
        )
        self.stdout.write(f"보관 기간: {days}일")
        self.stdout.write(f"삭제 기준 날짜: {cutoff_date}")
        self.stdout.write(f"배치 크기: {batch_size}")

        old_logs_query = BookingLog.objects.filter(created_at__lt=cutoff_dt)
        total_count = old_logs_query.count()

        if total_count == 0:
            self.stdout.write(self.style.SUCCESS("삭제할 오래된 로그가 없습니다."))
            return

        total_logs = BookingLog.objects.count()
        self.stdout.write(f"삭제 대상 로그: {total_count:,}개")
        self.stdout.write(f"전체 로그: {total_logs:,}개")

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f"[DRY RUN] {total_count:,}개의 로그가 삭제될 예정입니다.")
            )
            return

        if not force:
            confirm = input(f"\n{total_count:,}개의 로그를 삭제하시겠습니까? (y/N): ")
            if confirm.lower() not in ['y', 'yes']:
                self.stdout.write("삭제가 취소되었습니다.")
                return

        try:
            deleted_total, _ = cleanup_old_booking_logs(days=days, batch_size=batch_size)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"삭제 중 오류 발생: {str(e)}"))
            logger.error(f"BookingLog cleanup failed: {str(e)}")
            raise CommandError(f"삭제 실패: {str(e)}")

        remaining_logs = BookingLog.objects.count()
        self.stdout.write(self.style.SUCCESS("\n✅ 로그 정리 완료!"))
        self.stdout.write(f"삭제된 로그: {deleted_total:,}개")
        self.stdout.write(f"남은 로그: {remaining_logs:,}개")
        logger.info(
            f"BookingLog cleanup completed: {deleted_total} logs deleted, "
            f"{remaining_logs} logs remaining"
        )