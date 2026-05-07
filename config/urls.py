from django.contrib import admin
from django.urls import path, include
from ninja import NinjaAPI
from accounts.api import router as accounts_router
from campaigns.api import router as campaigns_router
from buyers.api import router as buyers_router
from publishers.api import router as publishers_router
from phone_numbers.api import router as phone_numbers_router
from routing.api import router as routing_router
from ivr.api import router as ivr_router

api = NinjaAPI(title="Call Platform API", version="1.0.0")

api.add_router("/accounts/", accounts_router)
api.add_router("/campaigns/", campaigns_router)
api.add_router("/buyers/", buyers_router)
api.add_router("/publishers/", publishers_router)
api.add_router("/numbers/", phone_numbers_router)
api.add_router("/routing/", routing_router)
api.add_router("/ivr/", ivr_router)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api.urls),
    path('api/twilio/', include('routing.urls')),
]