
from .settings import *


SECRET_KEY = "FF54QF564f54F56f4S5F4SDQkjkfjqfijFfjJfkJFKj"

# DATABASES = {
#     "default": dj_database_url.config(
#         default="postgres://blackflame:mypassword@/cloudsql/buoyant-aileron-261621:europe-west1:zerowingdb:5432/candlelight", conn_max_age=600
#     )
# }

ALLOWED_HOSTS = get_list(os.environ.get("ALLOWED_HOSTS", "*"))
