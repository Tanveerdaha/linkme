# Celery worker / beat operational notes for LinkMe.
#
# Queues:
#   default            — general async work
#   media_processing   — image/video FFmpeg + Pillow
#   notifications      — notification fan-out
#   exports            — user / admin data exports
#   cleanup            — retention + token blacklist
#
# Start workers (production compose already wires these):
#
#   celery -A config worker -Q default --concurrency=4
#   celery -A config worker -Q media_processing --concurrency=2
#   celery -A config worker -Q notifications,exports,cleanup --concurrency=4
#   celery -A config beat --loglevel=info
#
# Monitoring:
#   celery -A config inspect active
#   celery -A config inspect stats
#   celery -A config flower   # optional; install flower in prod extras
