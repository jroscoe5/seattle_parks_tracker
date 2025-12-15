# Seattle Parks Tracker 🌲

A Django web app to visually track your visits to Seattle's public parks using an interactive Leaflet.js map.

## Features

- **Interactive Map**: View all Seattle parks on a Leaflet.js-powered map
- **Visit Tracking**: Record visits with dates, ratings, notes, and photos
- **Photo Uploads**: Attach photos to each park visit
- **Progress Stats**: See your completion percentage and visit history
- **Filtering**: Toggle between visited and unvisited parks
- **Marker Clustering**: Parks are clustered at zoom levels for better UX

## Screenshots

The app shows:
- Green filled markers for visited parks ✓
- Green outline markers for unvisited parks
- Popup details with park info, photos, and quick-add visit button
- Progress bar in the header

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Migrations

```bash
python manage.py migrate
```

### 3. Load Seattle Parks Data

```bash
# This will try Seattle's open data API first, then fall back to seed data
python manage.py load_parks
```

### 4. Create Admin User (Optional)

```bash
python manage.py createsuperuser
```

### 5. Run the Server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000` to see your parks map!

## Data Sources

The app pulls park data from:
1. **Primary**: Seattle GeoData ArcGIS Hub (Park Boundary Details)
2. **Fallback**: GitHub seattle-boundaries-data repository
3. **Local**: Included seed data with 35 popular Seattle parks

To refresh park data from Seattle's API:
```bash
python manage.py load_parks --clear
```

## Project Structure

```
seattle_parks_tracker/
├── manage.py
├── requirements.txt
├── data/
│   └── seattle_parks_seed.json       # Fallback park data
├── seattle_parks_tracker/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── parks/
│   ├── models.py                     # Park, Visit, VisitPhoto models
│   ├── views.py                      # Map, detail, AJAX endpoints
│   ├── forms.py                      # Visit form with photo upload
│   ├── urls.py
│   ├── admin.py                      # Admin configuration
│   └── management/commands/
│       └── load_parks.py             # Data import command
└── templates/parks/
    ├── map.html                      # Main interactive map
    ├── park_detail.html              # Individual park view
    └── add_visit.html                # Add visit form
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/` | Main map view |
| `/api/parks/geojson/` | GeoJSON of all parks |
| `/api/parks/<id>/` | Park details JSON |
| `/api/parks/<id>/visit/` | Add visit (POST) |
| `/parks/<id>/` | Park detail page |
| `/stats/` | Visit statistics |
| `/admin/` | Django admin |

## Customization

### Adding More Parks

Edit `data/seattle_parks_seed.json` or run `load_parks` when you have network access to Seattle's API.

### Changing Map Style

In `templates/parks/map.html`, swap the tile layer URL:

```javascript
// OpenStreetMap (default)
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {...})

// CartoDB Positron (light)
L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png', {...})

// CartoDB Dark Matter
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png', {...})
```

## Tech Stack

- **Backend**: Django 4.2
- **Database**: SQLite (default)
- **Map**: Leaflet.js 1.9.4
- **Clustering**: Leaflet.markercluster
- **Image Processing**: Pillow

## License

MIT - feel free to use for your own park tracking adventures!
