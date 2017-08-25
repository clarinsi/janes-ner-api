# -*- coding: utf-8 -*-
import requests

from src.helpers import generate_token

print requests.post('http://0.0.0.0:8084/api/v1/sl/tag',
                    data={'format':'json',
                          'text': "Žive naj vsi narodi, ki hrepene dočakat dan. Da koder sonce hodi prepir iz sveta bo pregnan.",
                          'request-id':  generate_token()},
                    headers={"Authorization": "48990c1962624ccf8d8783f65701417b"}).content

