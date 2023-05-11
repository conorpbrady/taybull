import os
from dotenv import load_dotenv

load_dotenv()

app_stage = os.environ['DJANGO_APP_STAGE']
if app_stage == 'prod':
    from .prod import *
else:
    from .dev import *
