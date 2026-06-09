from decouple import config

DATABASE_BACKEND = config('DATABASE_BACKEND', default='local')  # 'local', 'supabase'

if DATABASE_BACKEND == 'supabase':
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.config(
            default=config('DATABASE_URL'),
            engine='django.contrib.gis.db.backends.postgis',
            conn_max_age=600,
            ssl_require=True,
        )
    }

else:  # local
    DATABASES = {
        'default': {
            'ENGINE': 'django.contrib.gis.db.backends.postgis',
            'NAME': config('DB_NAME', default='reporta_health'),
            'USER': config('DB_USER', default='postgres'),
            'PASSWORD': config('DB_PASSWORD', default='postgres'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }