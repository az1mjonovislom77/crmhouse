from django.db import models
from common.base.models_base import TimeStampedModel


class CallRecord(TimeStampedModel):
    organization = models.ForeignKey(
        'organization.Organization',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='call_records',
    )
    calldate = models.DateTimeField(db_index=True)
    clid = models.CharField(max_length=255, null=True, blank=True)
    src = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    dst = models.CharField(max_length=50, null=True, blank=True)
    dcontext = models.CharField(max_length=100, null=True, blank=True)
    channel = models.CharField(max_length=255, null=True, blank=True)
    dstchannel = models.CharField(max_length=255, null=True, blank=True)
    lastapp = models.CharField(max_length=100, null=True, blank=True)
    lastdata = models.TextField(null=True, blank=True)
    duration = models.IntegerField(null=True, blank=True)
    billsec = models.IntegerField(null=True, blank=True)
    disposition = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    amaflags = models.IntegerField(null=True, blank=True)
    accountcode = models.CharField(max_length=100, null=True, blank=True)
    uniqueid = models.CharField(max_length=50, null=True, blank=True, unique=True)
    userfield = models.TextField(null=True, blank=True)
    recordingfile = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    cnum = models.CharField(max_length=50, null=True, blank=True)
    cnam = models.CharField(max_length=100, null=True, blank=True)
    outbound_cnum = models.CharField(max_length=50, blank=True, null=True)
    outbound_cnam = models.CharField(max_length=100, blank=True, null=True)
    dst_cnam = models.CharField(max_length=100, blank=True, null=True)
    did = models.CharField(max_length=50, blank=True, null=True)
    audio_file = models.FileField(upload_to='call_records/', null=True, blank=True)
    audio_downloaded = models.BooleanField(default=False)

    @property
    def audio_url(self):
        if self.audio_file:
            return self.audio_file.url
        return None

    class Meta:
        verbose_name = 'Call Detail Record'
        verbose_name_plural = 'Call Detail Records'
        ordering = ['-calldate']

    def __str__(self):
        return f"{self.src} - {self.disposition}"
