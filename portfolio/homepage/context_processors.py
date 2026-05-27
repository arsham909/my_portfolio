from .models import SiteConfig


def site_config(request):
    """Expose the SiteConfig singleton to all templates as `site_config`."""
    return {'site_config': SiteConfig.load()}
