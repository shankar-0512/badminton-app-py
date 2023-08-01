from django.urls import path
from . import views

urlpatterns = [
    path('hello/', views.hello_view, name='hello'),
    path('json/', views.json_example, name='json_example'),
    path('greet/', views.greet, name='greet'),
    path('generate_pairing/', views.generate_pairing, name='generatePairing'),
    path('addToPool/', views.add_to_pool, name='addToPool'),
]