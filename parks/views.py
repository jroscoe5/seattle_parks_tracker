from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Max
import json

from .models import Park, Sign, Visit, VisitPhoto
from .forms import VisitForm, VisitPhotoForm


def map_view(request):
    """Main map view showing all parks."""
    parks = Park.objects.annotate(
        total_visits=Count('visits'),
        last_visited=Max('visits__visit_date')
    ).all()
    
    # Calculate stats
    total_parks = parks.count()
    visited_parks = parks.filter(total_visits__gt=0).count()
    completion_percentage = (visited_parks / total_parks * 100) if total_parks > 0 else 0
    
    context = {
        'parks': parks,
        'total_parks': total_parks,
        'visited_parks': visited_parks,
        'completion_percentage': round(completion_percentage, 1),
    }
    return render(request, 'parks/map.html', context)


def parks_geojson(request):
    """Return all parks as GeoJSON for the map."""
    parks = Park.objects.annotate(
        total_visits=Count('visits'),
        last_visited=Max('visits__visit_date')
    ).all()

    features = []
    for park in parks:
        # Get first photo if visited
        first_photo = None
        if park.total_visits > 0:
            latest_visit = park.visits.order_by('-visit_date').first()
            if latest_visit and latest_visit.photos.exists():
                first_photo = latest_visit.photos.first().image.url

        # Parse boundary GeoJSON if available
        boundary = None
        if park.boundary_geojson:
            try:
                boundary = json.loads(park.boundary_geojson)
            except json.JSONDecodeError:
                boundary = None

        # Get signs with their visit status
        signs_data = []
        for sign in park.signs.all():
            signs_data.append({
                'id': sign.id,
                'latitude': sign.latitude,
                'longitude': sign.longitude,
                'sign_type': sign.sign_type,
                'visited': sign.is_visited,
                'visit_count': sign.visit_count,
            })

        feature = {
            'type': 'Feature',
            'properties': {
                'id': park.id,
                'name': park.name,
                'address': park.address or '',
                'acres': park.acres,
                'park_type': park.park_type or '',
                'neighborhood': park.neighborhood or '',
                'visited': park.total_visits > 0,
                'visit_count': park.total_visits,
                'last_visited': park.last_visited.isoformat() if park.last_visited else None,
                'first_photo': first_photo,
                'has_rainbow_sign': park.has_rainbow_sign,
                'boundary': boundary,
                'signs': signs_data,
            },
            'geometry': {
                'type': 'Point',
                'coordinates': [park.longitude, park.latitude]
            }
        }
        features.append(feature)

    geojson = {
        'type': 'FeatureCollection',
        'features': features
    }

    return JsonResponse(geojson)


def park_detail(request, pk):
    """View park details and visits."""
    park = get_object_or_404(Park, pk=pk)
    visits = park.visits.prefetch_related('photos').all()
    
    context = {
        'park': park,
        'visits': visits,
    }
    return render(request, 'parks/park_detail.html', context)


def park_detail_json(request, pk):
    """Return park details as JSON for popups."""
    park = get_object_or_404(Park, pk=pk)
    visits = park.visits.prefetch_related('photos').select_related('sign').all()

    visits_data = []
    for visit in visits:
        photos = [{'url': photo.image.url, 'caption': photo.caption} for photo in visit.photos.all()]
        visits_data.append({
            'id': visit.id,
            'date': visit.visit_date.isoformat(),
            'notes': visit.notes or '',
            'rating': visit.rating,
            'photos': photos,
            'sign_id': visit.sign_id,
        })

    signs_data = []
    for sign in park.signs.all():
        signs_data.append({
            'id': sign.id,
            'latitude': sign.latitude,
            'longitude': sign.longitude,
            'sign_type': sign.sign_type,
            'visited': sign.is_visited,
        })

    data = {
        'id': park.id,
        'name': park.name,
        'address': park.address,
        'acres': park.acres,
        'park_type': park.park_type,
        'neighborhood': park.neighborhood,
        'latitude': park.latitude,
        'longitude': park.longitude,
        'visits': visits_data,
        'signs': signs_data,
    }

    return JsonResponse(data)


def park_signs_json(request, pk):
    """Return signs for a park as JSON."""
    park = get_object_or_404(Park, pk=pk)

    signs_data = []
    for sign in park.signs.all():
        signs_data.append({
            'id': sign.id,
            'latitude': sign.latitude,
            'longitude': sign.longitude,
            'sign_type': sign.sign_type,
            'visited': sign.is_visited,
            'label': f"{sign.sign_type} sign #{sign.id}",
        })

    return JsonResponse({'signs': signs_data})


@staff_member_required
@require_http_methods(["GET", "POST"])
def add_visit(request, park_id):
    """Add a new visit to a park. Restricted to admin users."""
    park = get_object_or_404(Park, pk=park_id)

    if request.method == 'POST':
        form = VisitForm(request.POST, park=park)
        if form.is_valid():
            visit = form.save(commit=False)
            visit.park = park
            visit.save()

            # Handle multiple photo uploads
            photos = request.FILES.getlist('photos')
            for photo in photos:
                VisitPhoto.objects.create(
                    visit=visit,
                    image=photo,
                )

            messages.success(request, f'Visit to {park.name} recorded!')

            # Return JSON response for AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Visit to {park.name} recorded!',
                    'visit_id': visit.id
                })

            return redirect('map_view')
    else:
        form = VisitForm(park=park)

    context = {
        'park': park,
        'form': form,
    }

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'parks/partials/visit_form.html', context)

    return render(request, 'parks/add_visit.html', context)


@staff_member_required
@require_http_methods(["POST"])
def add_visit_ajax(request, park_id):
    """AJAX endpoint for adding a visit with photos. Restricted to admin users."""
    park = get_object_or_404(Park, pk=park_id)

    form = VisitForm(request.POST, park=park)
    if form.is_valid():
        visit = form.save(commit=False)
        visit.park = park
        visit.save()

        # Handle multiple photo uploads
        photos = request.FILES.getlist('photos')
        photo_urls = []
        for photo in photos:
            visit_photo = VisitPhoto.objects.create(
                visit=visit,
                image=photo,
            )
            photo_urls.append(visit_photo.image.url)

        return JsonResponse({
            'success': True,
            'message': f'Visit to {park.name} recorded!',
            'visit_id': visit.id,
            'photos': photo_urls,
        })

    return JsonResponse({
        'success': False,
        'errors': form.errors,
    }, status=400)


def stats_view(request):
    """View statistics about park visits."""
    parks = Park.objects.annotate(
        total_visits=Count('visits')
    )
    
    total_parks = parks.count()
    visited_parks = parks.filter(total_visits__gt=0).count()
    unvisited_parks = total_parks - visited_parks
    total_visits = Visit.objects.count()
    total_photos = VisitPhoto.objects.count()
    
    # Most visited parks
    most_visited = parks.filter(total_visits__gt=0).order_by('-total_visits')[:10]
    
    # Recently visited
    recent_visits = Visit.objects.select_related('park').prefetch_related('photos')[:10]
    
    context = {
        'total_parks': total_parks,
        'visited_parks': visited_parks,
        'unvisited_parks': unvisited_parks,
        'total_visits': total_visits,
        'total_photos': total_photos,
        'completion_percentage': round(visited_parks / total_parks * 100, 1) if total_parks > 0 else 0,
        'most_visited': most_visited,
        'recent_visits': recent_visits,
    }
    return render(request, 'parks/stats.html', context)
