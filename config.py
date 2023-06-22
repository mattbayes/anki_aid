import redis
from os import environ

DOWNLOAD_FOLDER = "downloads"
# Database
SQLALCHEMY_DATABASE_URI = "sqlite:///language.db"

# File upload size
MAX_CONTENT_LENGTH = 16 * 1000 * 1000

# Mail
MAIL_SERVER = "smtp.gmail.com"
MAIL_PORT = 465
MAIL_USE_TLS = False
MAIL_USE_SSL = True
MAIL_USERNAME = environ.get("MAIL_USERNAME")
MAIL_PASSWORD = environ.get("MAIL_PASSWORD")
MAIL_DEFAULT_SENDER = environ.get("MAIL_DEFAULT_SENDER")

#Mail (testing)
TESTING = True
MAIL_SURPRESS_SEND = True

# Redis session
SECRET_KEY = "k2CTM-kJnW5JUI16gtMh_Q"
SESSION_TYPE = "redis"
SESSION_PERMANENT = False
#app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=24)
#SESSION_USE_SIGNER = True
SESSION_REDIS = redis.Redis(host="127.0.0.1",port=6379)