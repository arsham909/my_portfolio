import re

from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse


IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp', 'gif']

YOUTUBE_ID_RE = re.compile(
    r'(?:youtube\.com/(?:watch\?v=|embed/|shorts/|live/)|youtu\.be/)([A-Za-z0-9_-]{11})'
)


class PublishedProjectManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_published=True)


class Project(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    summary = models.CharField(
        max_length=300,
        help_text='Short tagline shown on the home card (1-2 sentences).',
    )
    tech = models.CharField(
        max_length=300,
        blank=True,
        help_text='Stack list, e.g. "Python · Django · AWS Lambda".',
    )
    body = models.TextField(
        blank=True,
        help_text='Full description (Markdown). Shown on the project detail page.',
    )
    cover_image = models.ImageField(
        upload_to='projects/cover/',
        validators=[FileExtensionValidator(IMAGE_EXTENSIONS)],
        help_text='Image shown on the home page card.',
    )
    github_url = models.URLField(blank=True)
    demo_url = models.URLField(
        blank=True,
        help_text='Optional live-demo link.',
    )
    youtube_url = models.URLField(
        blank=True,
        help_text='Optional YouTube demo video URL — embedded on the detail page.',
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text='Lower numbers appear first.',
    )
    is_featured = models.BooleanField(
        default=False,
        help_text='Show on the home page featured grid.',
    )
    is_published = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    objects = models.Manager()
    published = PublishedProjectManager()

    class Meta:
        ordering = ['order', '-created']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('homepage:project_detail', args=[self.slug])

    @property
    def youtube_embed_id(self):
        if not self.youtube_url:
            return ''
        m = YOUTUBE_ID_RE.search(self.youtube_url)
        return m.group(1) if m else ''


class ProjectImage(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='images',
    )
    image = models.ImageField(
        upload_to='projects/gallery/',
        validators=[FileExtensionValidator(IMAGE_EXTENSIONS)],
    )
    caption = models.CharField(max_length=200, blank=True)
    alt_text = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created']

    def __str__(self):
        return f'Image #{self.pk} — {self.project.title}'


class SiteConfig(models.Model):
    """Site-wide editable settings. Enforced singleton (pk=1)."""

    resume_file = models.FileField(
        upload_to='resume/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(['pdf'])],
        help_text='Upload your latest resume PDF. Replaces the previous file.',
    )
    resume_label = models.CharField(max_length=80, default='Download Resume')
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Site configuration'
        verbose_name_plural = 'Site configuration'

    def save(self, *args, **kwargs):
        # Enforce singleton: one row keeps admin + templates unambiguous.
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return 'Site configuration'
