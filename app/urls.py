from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login, name='login'),
    path('signup/', views.signup, name='signup'),
    path('generatePairing/', views.generate_pairing, name='generatePairing'),
    path('addToPool/', views.add_to_pool, name='addToPool'),
    path('removeFromPool/', views.remove_from_pool, name='removeFromPool'),
    path('fetchActivePlayers/', views.fetch_active_players,
         name='fetchActivePlayers'),
    path('updateElo/', views.update_elo, name='updateElo'),
    path('resetDatabase/', views.reset_database, name='resetDatabase'),
    path('getCourtStatus/', views.get_court_status, name='getCourtStatus'),
    path('navigateToCourtScreen/', views.navigate_to_court_screen, name='navigateToCourtScreen'),
]
