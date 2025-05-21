from flask import Flask

app = Flask(__name__)

# Import routes setelah app dibuat
from app import routes
