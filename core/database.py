import os
from dotenv import load_dotenv

def __init__(self):
    load_dotenv()
    self.host = os.getenv(SQL)
    self.user = "root"
    self.connection = None