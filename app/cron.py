def clear_history():
    from .models import History
    History.objects.all().delete()
