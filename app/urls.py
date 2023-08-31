from django.urls import path
from . import views

urlpatterns = [
    # Authentication related endpoints
    path('login/', views.login, name='login'),
    path('signup/', views.signup, name='signup'),

    # Player related endpoints
    path('addToPool/', views.add_to_pool, name='addToPool'),
    path('removeFromPool/', views.remove_from_pool, name='removeFromPool'),
    path('fetchActivePlayers/', views.fetch_active_players, name='fetchActivePlayers'),
    path('fetchUserDetails/', views.fetch_user_data, name='fetchUserDetails'),

    # Match related endpoints
    path('generatePairing/', views.generate_pairing, name='generatePairing'),
    path('updateElo/', views.update_elo, name='updateElo'),
    
    # Court related endpoints
    path('getCourtStatus/', views.get_court_status, name='getCourtStatus'),
    path('navigateToCourtScreen/', views.navigate_to_court_screen, name='navigateToCourtScreen'),

    # Utility or admin related endpoints
    path('resetDatabase/', views.reset_database, name='resetDatabase'),
    #path('runSimulation/', views.run_simulation, name='runSimulation'),
]
