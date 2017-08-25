from ..helpers import jsonify, TCF, jsonTCF, isset
from lxml import etree
from StringIO import StringIO

from flask import Blueprint
from flask import request
from flask import Response
from flask import current_app
from functools import wraps
from ..models.user_model import UserModel
from ..models.auth_token_model import AuthTokenModel
import re
import os
import json
import csv


class ServerError(Exception):
    """
    Thrown during a 500 server error
    """
    status_code = 500

    def __init__(self, message):
        '''
        @param message: The exception message to be shown
        @type message: string
        '''
        Exception.__init__(self)
        self.message = message

    def to_dict(self):
        '''

        @return:
        @rtype: string
        '''
        rv = dict()
        rv['message'] = self.message
        return rv


class Unauthorized(Exception):
    """
    Thrown during a 401 server error
    """
    status_code = 401

    def __init__(self, message):
        '''
        @param message: The exception message to be shown
        @type message: string

        '''
        Exception.__init__(self)
        self.message = message

    def to_dict(self):
        '''
        @return:
        @rtype: string
        '''
        rv = dict()
        rv['message'] = self.message
        return rv


class InvalidUsage(Exception):
    """
    Thrown during a 422 server error
    """
    status_code = 422

    def __init__(self, message):
        '''
        @param message:
        @type message: string
        '''
        Exception.__init__(self)
        self.message = message

    def to_dict(self):
        '''

        @return:
        @rtype: string
        '''
        rv = dict()
        rv['message'] = self.message
        return rv


class ApiRouter(Blueprint):

    def register(self, app, options, first_registration=False):
        super(ApiRouter, self).register(app, options, first_registration=False)
        self.config = app.config

    def __init__(self, dc):
        '''Routes HTTP requests to specific calls to the internal core/api classes

        @param dc: dependency injection container with initialized core objects
        @type dc: DependencyContainer
        '''
        Blueprint.__init__(self, 'api_router', 'api_router')
        self.config = {}

        def authenticate(api_method):
            '''
            The method is executed before each HTTP API call.
            If a valid cookie or authentication header is not set, an Unauthorized Exception will be thrown.

            @param api_method:
            @type api_method: string
            @return:
            @rtype: string
            '''

            @wraps(api_method)
            def verify(*args, **kwargs):
                '''

                @param args:
                @type args: string
                @param kwargs:
                @type kwargs: string
                @return:
                @rtype: string
                '''
                auth_token_string = request.cookies.get('auth-token')
                if auth_token_string is None:
                    auth_token_string = request.headers.get('Authorization')

                if auth_token_string is None:
                    raise Unauthorized('Invalid token')

                authToken = AuthTokenModel.getByAttributeSingle('token', auth_token_string)
                if authToken is None or not authToken.isValid():
                    raise Unauthorized('Invalid token')

                # Log request
                user = UserModel.getByPk(authToken.user_id)
                if user is None:
                    raise Unauthorized('Invalid token')

                if user.status != 'active':
                    raise Unauthorized('User has no access')

                user.logRequest()
                user.save()
                return api_method(*args, **kwargs)

            return verify

        def save_file(api_method):
            @wraps(api_method)
            def post_request(*args, **kwargs):
                auth_token_string = request.cookies.get('auth-token')
                if auth_token_string is None:
                    auth_token_string = request.headers.get('Authorization')

                if auth_token_string is None:
                    raise Unauthorized('Invalid token')

                authToken = AuthTokenModel.getByAttributeSingle('token', auth_token_string)
                if authToken is None or not authToken.isValid():
                    raise Unauthorized('Invalid token')

                result = api_method(*args, **kwargs)
                filePath = os.path.join(self.config['UPLOAD_FOLDER'], get_request_id(request))

                raw = result.get_data()
                try:
                    data = json.loads(raw)
                    csvResult = []
                    posTags = {}
                    lemmas = {}
                    tokens = {}

                    if 'POSTags' in data:
                        for tag in data['POSTags']:
                            posTags[tag['tokenIDs']] = tag

                    if 'lemmas' in data:
                        for lemma in data['lemmas']:
                            lemmas[lemma['tokenIDs']] = lemma

                    if 'tokens' in data:
                        for token in data['tokens']:
                            tokens[token['ID']] = token

                    for sentence in data['sentences']:
                        for tid in sentence['tokenIDs'].split(' '):
                            csvResult.append([])
                            token = tokens[tid]
                            csvResult[-1].append(token['value'])
                            if tid in posTags:
                                csvResult[-1].append(posTags[tid]['value'])
                            if tid in lemmas:
                                csvResult[-1].append(lemmas[tid]['value'])
                            csvResult[-1].append(token['startChar'] + ' - ' + token['endChar'])
                        csvResult.append([])

                    with open(filePath, 'w') as f:
                        w = csv.writer(f, delimiter="\t")
                        w.writerows(csvResult)

                except:
                    with open(filePath, 'w') as f:
                        f.write(raw)

                return result

            return post_request

        def get_format(request):
            params = request.form if request.method == 'POST' else request.args
            format = params.get('format')
            return format

        def get_request_id(request):
            params = request.form if request.method == 'POST' else request.args
            request_id = params.get('request-id')
            if not isset(request_id):
                raise InvalidUsage('Please specify a request id')

            return request_id

        def get_text(format, request):
            '''

            @param format:
            @type format: string
            @param request:
            @type request: string
            @return:
            @rtype: string
            '''
            print "get text"
            params = request.form if request.method == 'POST' else request.args
            files = request.files
            if format == 'json':
                if 'file' in files:
                    return files['file'].read()
                else:
                    return params.get('text')
            elif format == 'tcf':
                with open('assets/tcfschema/d-spin-local_0_4.rng', 'r') as f:

                    if 'file' in files:
                        text = files['file'].read()
                    else:
                        text = params.get('text').encode('utf-8')
                    relaxng_doc = etree.parse(f)
                    relaxng = etree.RelaxNG(relaxng_doc)
                    inputXml = re.sub(">\\s*<", "><", text)
                    inputXml = re.sub("^\\s*<", "<", inputXml)

                    doc = etree.parse(StringIO(inputXml))
                    try:
                        relaxng.assertValid(doc)
                        return doc.getroot()[1][0].text
                    except Exception as e:
                        raise InvalidUsage(e.message)
            else:
                raise InvalidUsage('Unknown format ' + format)

        @self.route('/')
        def index():
            '''

            @return:
            @rtype: string
            '''
            return "Main"

        # @self.errorhandler(Exception)
        # def handle_error(error):
        #     '''
        #
        #     @param error:
        #     @type error: string
        #     @return:
        #     @rtype: string
        #     '''
        #     raise error
        #     current_app.logger.error(error)
        #     response = jsonify(error.message)
        #     return response, error.status_code if hasattr(error, 'status_code') else 500


        @self.route('/<lang>/tag', methods=['GET', 'POST'])
        @authenticate
        @save_file
        def tag(lang):
            '''

            @param lang:
            @type lang: string
            @return:
            @rtype: string
            '''

            format = get_format(request)
            if not isset(format):
                raise InvalidUsage('Please specify a format')

            text = get_text(format, request)
            tagger = dc['tagger.' + lang]
            print "2"
            result = tagger.tag(text)
            print "3"
            if format == 'json':
                return jsonify(jsonTCF(lang, text, result, tag_idx=1), ensure_ascii=False)
            elif format == 'tcf':
                return Response(TCF(lang, text, result, tag_idx=1), mimetype='text/xml')


        @self.route('/login', methods=['POST'])
        def login():
            '''

            @return:
            @rtype: string
            '''
            username = request.form.get('username')
            password = request.form.get('password')

            if username is None or password is None:
                raise Unauthorized("Invalid username or password")
            user = UserModel.getByUsername(username)
            if user is None:
                raise Unauthorized("Invalid username or password")
            else:
                try:
                    token = user.generateToken(password)
                    token.save()
                    return jsonify(token.token, ensure_ascii=False)
                except ValueError as e:
                    raise Unauthorized(e.__str__())
