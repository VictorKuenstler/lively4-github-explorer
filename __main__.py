import os

from server.controller import api
from dotenv import load_dotenv

load_dotenv()

if __name__ == '__main__':
    api.run(port=os.environ['PORT'])
