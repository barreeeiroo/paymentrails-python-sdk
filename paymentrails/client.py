
import time
import hmac
import hashlib
import json
import requests

from paymentrails.exceptions.invalidFieldException import InvalidFieldException
from paymentrails.exceptions.unexpectedException import UnexpectedException
from paymentrails.exceptions.notFoundException import NotFoundException
from paymentrails.exceptions.authenticationException import AuthenticationException
from paymentrails.exceptions.authorizationException import AuthorizationException
from paymentrails.exceptions.invalidFieldException import InvalidFieldException
from paymentrails.exceptions.tooManyRequestsException import TooManyRequestsException
from paymentrails.exceptions.downForMaintenanceException import DownForMaintenanceException
from paymentrails.exceptions.malformedException import MalformedException
from paymentrails.exceptions.invalidStatusException import InvalidStatusException
from paymentrails.exceptions.invalidServerConnectionException import InvalidServerConnectionException


class Client(object):
    """
    A class that makes Client requests to the API.
    """

    def __init__(self, config):
        self.config = config

    @staticmethod
    def create(config):
        """
        Factory create method
        """
        return Client(config)

    def sendRequest(self,endpoint,method,body=""):
        try:
            timestamp = int(time.time())
            authorization = self.generate_authorization(timestamp, method, endpoint, self.config, body)

            headers = {'Content-Type': 'application/json',
                       'Authorization': authorization,
                       'X-PR-Timestamp': str(timestamp)}
            
            if method == "GET":
                request = requests.get(self.config.enviroment + endpoint, headers=headers)
            elif method == "POST":
                request = requests.post(self.config.enviroment + endpoint, headers=headers, json=body)
            elif method == "PATCH":
                request = requests.patch(self.config.enviroment + endpoint, headers=headers, json=body)
            elif method == "DELETE":
                request = requests.delete(self.config.enviroment + endpoint, headers=headers)
            else:
                self.throw_status_code_exception(None, "Invalid Method")
            if request.status_code != 200 and request.status_code != 204:
                self.throw_status_code_exception(request.status_code, request.content.decode("utf-8"))

            data = json.loads(request.content.decode("utf-8"))
            return data

        except requests.exceptions.RequestException:
            raise InvalidServerConnectionException("Invalid Connection to the server")

    def get(self, endpoint):
        """
        Makes an HTTP GET request to the API
        """
        return self.sendRequest(endpoint,"GET")

    def post(self, endpoint, body):
        """
        Makes an HTTP POST request to the API
        """
        return self.sendRequest(endpoint,"POST",body)

    def patch(self, endpoint, body):
        """
        Makes an HTTP PATCH request to the API
        """
        return self.sendRequest(endpoint,"PATCH",body)   

    def delete(self, endpoint):
        """
        Makes an HTTP DELETE request to the API
        """
        return self.sendRequest(endpoint,"DELETE")

    def generate_authorization(self,timestamp, method, endpoint, config, body=''):
        """
        Generates an authorization signature for the request header
        """
        if body != '':
            body = json.dumps(body)
        message = str(timestamp) + '\n' + method + \
            '\n' + endpoint + '\n' + body + '\n'
        key = bytes(self.config.private_key.encode('utf-8'))
        signature = hmac.new(key, msg=message.encode(
            'utf-8'), digestmod=hashlib.sha256).hexdigest()
        return 'prsign ' + self.config.public_key + ':' + signature
    @staticmethod
    def throw_status_code_exception(status_code, message):
        """
        Throws an exception based on the type of error
        """
        if status_code == 400:
            raise MalformedException(message)
        elif status_code == 401:
            raise AuthenticationException(message)
        elif status_code == 403:
            raise AuthorizationException(message)
        elif status_code == 404:
            raise NotFoundException(message)
        elif status_code == 406:
            raise InvalidStatusException(message)
        elif status_code == 429:
            raise TooManyRequestsException(message)
        elif status_code == 500:
            raise InvalidServerConnectionException(message)
        elif status_code == 503:
            raise DownForMaintenanceException(message)
        else:
            raise UnexpectedException(
                'Unexpected HTTP_RESPONSE # ' + str(status_code) + " " + message)
