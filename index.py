# -*- coding: utf-8 -*-
import sys
import os
from flask import Flask
from flask.ext.cors import CORS

from src.core.segmenter import Segmenter
from src.core.tagger import Tagger
from src.core.ner_tagger import NerTagger
from src.di import DependencyContainer

# from src.core.lexicon import Lexicon
# from src.core.segmenter import Segmenter
# from src.core.tagger import Tagger
# from src.core.lematiser import Lematiser

from src.routers.api_router import ApiRouter
from src.helpers import jsonify

from flask import make_response, redirect
import traceback

reload(sys)
sys.setdefaultencoding('utf-8')

def init():
    app = Flask(__name__)
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['UPLOAD_FOLDER'] = os.path.dirname(os.path.realpath(__file__)) + '/uploads/'

    CORS(app)

    print 'Initializing models'
    dc = DependencyContainer(lazy=False)
    for lang in ['sl']: #['hr', 'sl', 'sr']:
        dc['segmenter.' + lang] = lambda: Segmenter(lang)
        dc['tagger.' + lang] = lambda: Tagger(lang, dc['segmenter.' + lang])
        dc['ner_tagger.' + lang] = lambda: NerTagger(lang, dc['tagger.' + lang])


    print 'Models initialized'

    api_router = ApiRouter(dc)
    app.register_blueprint(api_router, url_prefix='/api/v1')


    @app.errorhandler(Exception)
    def handle_error(error):
        '''
        @param error:
        @type error: string
        @return:
        @rtype: string
        '''
        app.logger.error(error)
        traceback.print_exc()
        response = jsonify(error.message)
        return response, error.status_code if hasattr(error, 'status_code') else 500

    @app.route('/', methods=['GET'])
    def main():
        return make_response(redirect('/api'))

    return app


application = init()
#application.run()

if __name__ == "__main__":

    text = 'Modeli su učitani! Vrlo uspješno.'

    # lemmatiser = dc['lemmatiser.hr']
    # tagger = dc['tagger.hr']
    # segmenter = dc['segmenter.hr']
    # lexicon = dc['lexicon.hr']

    # print lemmatiser.tagLemmatise(text)
    # print lemmatiser.lemmatise(text)
    # print tagger.tag(text)
    # print segmenter.segment(text)

    app = init()
    app.run(host='0.0.0.0', port=8084, debug=True)
