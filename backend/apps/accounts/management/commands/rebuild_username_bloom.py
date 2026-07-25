"""Rebuild the Redis Bloom filter of usernames from PostgreSQL."""

from django.core.management.base import BaseCommand

from apps.accounts.bloom import get_username_bloom


class Command(BaseCommand):
    help = "Rebuild linkme:usernames Redis Bloom filter from the User table."

    def handle(self, *args, **options):
        bloom = get_username_bloom()
        if not bloom.enabled:
            self.stderr.write(self.style.ERROR("REDIS_BLOOM_ENABLED is false"))
            return

        count = bloom.rebuild()
        self.stdout.write(
            self.style.SUCCESS(
                f"Rebuilt username bloom filter with {count} username(s)."
            )
        )
