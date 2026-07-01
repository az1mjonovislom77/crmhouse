import logging
import os
import tempfile
from datetime import date, timedelta

from celery import shared_task
from django.core.files import File

from .services import CDRService

logger = logging.getLogger(__name__)


@shared_task
def sync_cdr_data():
    today = date.today()
    start_date = today - timedelta(days=7)

    params = {
        'startdate': start_date.strftime('%Y-%m-%d'),
        'enddate': today.strftime('%Y-%m-%d'),
    }

    try:
        saved = CDRService.fetch_and_save_cdr(params)
        logger.info(f'CDR sync muvaffaqiyatli: {saved} ta yangi yozuv saqlandi')
    except Exception as e:
        logger.error(f'CDR sync xatosi: {str(e)}', exc_info=True)


@shared_task(bind=True, max_retries=3)
def download_recording_task(self, record_id):
    from contact_center.models import CallRecord
    from contact_center.services import IssabelService

    record = CallRecord.objects.get(id=record_id)

    if record.audio_downloaded or not record.recordingfile:
        return

    service = IssabelService()
    temp_path = None

    try:
        response = service.stream_recording(record.recordingfile)

        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            temp_path = tmp_file.name
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    tmp_file.write(chunk)

        with open(temp_path, 'rb') as f:
            filename = os.path.basename(record.recordingfile)
            record.audio_file.save(filename, File(f), save=False)

        record.audio_downloaded = True
        record.save(update_fields=['audio_file', 'audio_downloaded'])

    except Exception as e:
        raise self.retry(exc=e, countdown=60)

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
