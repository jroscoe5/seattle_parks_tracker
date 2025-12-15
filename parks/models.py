from django.db import models
from django.utils import timezone


class Park(models.Model):
    """Model representing a Seattle public park."""
    
    name = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()
    address = models.CharField(max_length=500, blank=True, null=True)
    acres = models.FloatField(blank=True, null=True)
    park_type = models.CharField(max_length=100, blank=True, null=True)
    neighborhood = models.CharField(max_length=100, blank=True, null=True)
    
    # GeoJSON polygon for park boundary (stored as JSON string)
    boundary_geojson = models.TextField(blank=True, null=True)
    
    # External ID from Seattle's data portal
    external_id = models.CharField(max_length=100, unique=True, blank=True, null=True)

    # PMA ID from Seattle Parks (for matching with signs)
    pma_id = models.CharField(max_length=20, unique=True, blank=True, null=True)

    # Track if park has a rainbow sign
    has_rainbow_sign = models.BooleanField(default=False)

    # JSON array of all rainbow sign coordinates [[lon, lat], ...]
    rainbow_sign_locations = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def is_visited(self):
        """Check if park has been visited."""
        return self.visits.exists()
    
    @property
    def visit_count(self):
        """Get total number of visits."""
        return self.visits.count()
    
    @property
    def latest_visit(self):
        """Get the most recent visit."""
        return self.visits.order_by('-visit_date').first()


class Sign(models.Model):
    """Model representing a sign at a park (e.g., rainbow sign)."""

    park = models.ForeignKey(Park, on_delete=models.CASCADE, related_name='signs')
    latitude = models.FloatField()
    longitude = models.FloatField()
    sign_type = models.CharField(max_length=50, default='RAINBOW')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['park__name']

    def __str__(self):
        return f"{self.sign_type} sign at {self.park.name}"

    @property
    def is_visited(self):
        """Check if this sign has been visited."""
        return self.visits.exists()

    @property
    def visit_count(self):
        """Get total number of visits to this sign."""
        return self.visits.count()


class Visit(models.Model):
    """Model representing a visit to a park."""

    park = models.ForeignKey(Park, on_delete=models.CASCADE, related_name='visits')
    sign = models.ForeignKey(
        Sign,
        on_delete=models.SET_NULL,
        related_name='visits',
        blank=True,
        null=True,
        help_text="Optional: specific sign visited"
    )
    visit_date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True, null=True)
    rating = models.IntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],
        blank=True,
        null=True,
        help_text="Rating from 1-5 stars"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-visit_date']
    
    def __str__(self):
        return f"{self.park.name} - {self.visit_date}"


class VisitPhoto(models.Model):
    """Model representing a photo from a park visit."""
    
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='visit_photos/%Y/%m/')
    caption = models.CharField(max_length=255, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Photo from {self.visit.park.name} ({self.visit.visit_date})"
