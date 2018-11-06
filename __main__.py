import os

from dotenv import load_dotenv
load_dotenv()

from server.controller import api

if __name__ == '__main__':
    api.run(port=os.environ['PORT'])
