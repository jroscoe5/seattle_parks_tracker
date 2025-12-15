"""
Management command to load Seattle parks data from local GeoJSON files.

Uses:
- Park_Boundaries_*.geojson for park boundaries
- Park_Signs_*.geojson for rainbow sign locations
"""

import json
import os
from collections import defaultdict
from django.core.management.base import BaseCommand
from django.conf import settings
from parks.models import Park

from pyproj import Transformer


class Command(BaseCommand):
    help = 'Load Seattle parks data from local GeoJSON files'

    # File paths relative to BASE_DIR/data/
    BOUNDARIES_FILE = 'Park_Boundaries_8590650033188940041.geojson'
    SIGNS_FILE = 'Park_Signs_-5626504497805504009.geojson'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing parks before loading',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing parks...')
            Park.objects.all().delete()

        # Initialize coordinate transformer (EPSG:2926 -> EPSG:4326)
        # EPSG:2926 is Washington State Plane North (US feet)
        # EPSG:4326 is WGS84 (latitude/longitude)
        self.transformer = Transformer.from_crs("EPSG:2926", "EPSG:4326", always_xy=True)

        # Load GeoJSON files
        data_dir = os.path.join(settings.BASE_DIR, 'data')

        boundaries_path = os.path.join(data_dir, self.BOUNDARIES_FILE)
        signs_path = os.path.join(data_dir, self.SIGNS_FILE)

        self.stdout.write(f'Loading boundaries from: {boundaries_path}')
        with open(boundaries_path, 'r') as f:
            boundaries_data = json.load(f)

        self.stdout.write(f'Loading signs from: {signs_path}')
        with open(signs_path, 'r') as f:
            signs_data = json.load(f)

        # Build rainbow sign lookup: PMAID -> list of sign features
        # Group all rainbow signs by park (some parks have multiple)
        rainbow_signs = defaultdict(list)
        for feature in signs_data['features']:
            props = feature.get('properties', {})
            if props.get('SIGN_TP') == 'RAINBOW':
                pmaid = props.get('PMAID')
                if pmaid:
                    rainbow_signs[pmaid].append(feature)

        self.stdout.write(f'Found {sum(len(v) for v in rainbow_signs.values())} rainbow signs across {len(rainbow_signs)} parks')
        self.stdout.write(f'Processing {len(boundaries_data["features"])} park boundaries...')

        parks_created = 0
        parks_updated = 0
        parks_skipped = 0
        parks_with_signs = 0
        parks_without_signs = 0

        for feature in boundaries_data['features']:
            try:
                props = feature.get('properties', {})
                geometry = feature.get('geometry', {})

                # Extract park name
                name = props.get('NAME', 'Unknown Park')
                if not name or name == 'Unknown Park':
                    parks_skipped += 1
                    continue

                # Get PMA ID (integer in boundaries file)
                pma = props.get('PMA')
                if pma is None:
                    parks_skipped += 1
                    continue
                pma_str = str(pma)

                # Check if park has rainbow sign(s)
                park_signs = rainbow_signs.get(pma_str, [])
                has_rainbow_sign = len(park_signs) > 0

                if has_rainbow_sign:
                    parks_with_signs += 1
                else:
                    parks_without_signs += 1

                # Always use centroid of boundary for park marker location
                longitude, latitude = self.calculate_centroid_wgs84(geometry)

                # Collect all rainbow sign locations
                rainbow_sign_locations = []
                if has_rainbow_sign:
                    for sign in park_signs:
                        sign_coords = sign['geometry']['coordinates']
                        lon, lat = self.transform_point(sign_coords[0], sign_coords[1])
                        rainbow_sign_locations.append([lon, lat])

                # Validate coordinates are in Seattle area
                if not (-123 < longitude < -121 and 47 < latitude < 48):
                    self.stderr.write(f'Invalid coordinates for {name}: ({latitude}, {longitude})')
                    parks_skipped += 1
                    continue

                # Transform boundary geometry to WGS84 for storage
                transformed_geometry = self.transform_geometry(geometry)

                # Extract area and convert to acres
                area_sqft = props.get('PARKSBND_AREA')
                acres = None
                if area_sqft:
                    # Convert square feet to acres (1 acre = 43560 sq ft)
                    acres = round(area_sqft / 43560.0, 2)

                # External ID from OBJECTID
                external_id = str(props.get('OBJECTID', ''))

                # Create or update park
                park, created = Park.objects.update_or_create(
                    pma_id=pma_str,
                    defaults={
                        'name': name,
                        'latitude': latitude,
                        'longitude': longitude,
                        'acres': acres,
                        'external_id': external_id if external_id else None,
                        'boundary_geojson': json.dumps(transformed_geometry),
                        'has_rainbow_sign': has_rainbow_sign,
                        'rainbow_sign_locations': json.dumps(rainbow_sign_locations) if rainbow_sign_locations else None,
                    }
                )

                if created:
                    parks_created += 1
                else:
                    parks_updated += 1

            except Exception as e:
                self.stderr.write(f'Error processing feature: {e}')
                parks_skipped += 1
                continue

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Created: {parks_created}, Updated: {parks_updated}, Skipped: {parks_skipped}'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'Parks with rainbow signs: {parks_with_signs}, Parks without: {parks_without_signs}'
        ))

    def transform_point(self, x, y):
        """Transform a single point from EPSG:2926 to WGS84."""
        lon, lat = self.transformer.transform(x, y)
        return lon, lat

    def calculate_centroid_wgs84(self, geometry):
        """Calculate centroid of geometry and return in WGS84."""
        geom_type = geometry.get('type', '')
        coords = geometry.get('coordinates', [])

        try:
            if geom_type == 'MultiPolygon':
                # Use the first polygon's first ring
                ring = coords[0][0]
            elif geom_type == 'Polygon':
                # Use the first ring (outer boundary)
                ring = coords[0]
            else:
                return 0, 0

            # Calculate average of all points (simple centroid)
            x_sum = sum(point[0] for point in ring)
            y_sum = sum(point[1] for point in ring)
            count = len(ring)

            centroid_x = x_sum / count
            centroid_y = y_sum / count

            # Transform to WGS84
            return self.transform_point(centroid_x, centroid_y)

        except (IndexError, TypeError, ZeroDivisionError):
            return 0, 0

    def transform_geometry(self, geometry):
        """Transform entire geometry from EPSG:2926 to WGS84."""
        geom_type = geometry.get('type', '')
        coords = geometry.get('coordinates', [])

        if geom_type == 'Polygon':
            transformed_coords = [
                [list(self.transform_point(p[0], p[1])) for p in ring]
                for ring in coords
            ]
        elif geom_type == 'MultiPolygon':
            transformed_coords = [
                [
                    [list(self.transform_point(p[0], p[1])) for p in ring]
                    for ring in polygon
                ]
                for polygon in coords
            ]
        else:
            return geometry

        return {
            'type': geom_type,
            'coordinates': transformed_coords
        }
