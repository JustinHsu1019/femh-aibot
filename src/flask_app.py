import utils.config_log as config_log
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_httpauth import HTTPBasicAuth
from flask_restx import Api, Resource, fields
from utils.ai.call_ai import call_aied
from utils.weaviate_op import search_do
from werkzeug.security import check_password_hash, generate_password_hash

config, logger, CONFIG_PATH = config_log.setup_config_and_logging()
config.read(CONFIG_PATH)

auth = HTTPBasicAuth()

users = {'femh': generate_password_hash(config.get('Api_docs', 'password'))}


@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username
    return None


app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type, Qs-PageCode, Cache-Control'

api = Api(
    app,
    version='1.0',
    title='femh API',
    description='femh API'
)

ns = api.namespace('api', description='Chatbot operations')

model = api.model(
    'ChatRequest',
    {
        'message': fields.String(required=True, description='The message to the chatbot')
    },
)


@ns.route('/')
class HealthCheck(Resource):
    @api.doc('health_check')
    def get(self):
        """Server health check."""
        response = jsonify('server is ready')
        response.status_code = 200
        return response


@ns.route('/chat')
class ChatBot(Resource):
    @api.doc('chat_bot')
    @api.expect(model)
    def post(self):
        question = request.json.get('message')

        # pre1qa = request.json.get('pre1qa') or {'q': '', 'a': ''}
        # pre2qa = request.json.get('pre2qa') or {'q': '', 'a': ''}

        alpha = 0.8

        use_gpt = True

        if not question:
            response = jsonify({'llm': '無問題', 'retriv': '無檢索'})
            response.status_code = 200
            return response
        else:
            combined_query_str = question
            # combined_query_str = (
            #     f"【前次問答】\n"
            #     f"Q: {pre2qa.get('q', '')}\n"
            #     f"A: {pre2qa.get('a', '')}\n\n"
            #     f"【上次問答】\n"
            #     f"Q: {pre1qa.get('q', '')}\n"
            #     f"A: {pre1qa.get('a', '')}\n\n"
            #     f"【當前問題】\n"
            #     f"QUESTION: {question}\n"
            # )
            try:
                response_li = search_do(question, alp=alpha)
                response = call_aied(response_li, combined_query_str, use_gpt)

                if not isinstance(response, str):
                    response = str(response)
                if not isinstance(response_li, str):
                    response_li = str(response_li)

            except Exception:
                response = jsonify({'message': 'Internal Server Error'})
                response.status_code = 500
                return response

        try:
            response = jsonify({'llm': response, 'retriv': response_li})
            response.status_code = 200
            return response
        except TypeError:
            response = jsonify({'message': 'Internal Server Error'})
            response.status_code = 500
            return response


@app.before_request
def require_auth_for_docs():
    if request.path == '/':
        return auth.login_required()(swagger_ui)()


@app.route('/')
def swagger_ui():
    return api.render_doc()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
