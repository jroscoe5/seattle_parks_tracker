from django.urls import path
from . import views

urlpatterns = [
    path('', views.map_view, name='map_view'),
    path('api/parks/geojson/', views.parks_geojson, name='parks_geojson'),
    path('api/parks/<int:pk>/', views.park_detail_json, name='park_detail_json'),
    path('parks/<int:pk>/', views.park_detail, name='park_detail'),
    path('parks/<int:park_id>/visit/', views.add_visit, name='add_visit'),
    path('api/parks/<int:park_id>/visit/', views.add_visit_ajax, name='add_visit_ajax'),
    path('stats/', views.stats_view, name='stats_view'),
]
