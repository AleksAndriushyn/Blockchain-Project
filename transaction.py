import requests

requests.post(url='http://localhost:5000/transactions/new',json={'sender':'Aleks','recipient':'Zheka','amount':99999}).text
