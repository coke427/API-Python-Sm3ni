from flask import Flask, request, jsonify
from flask_cors import CORS

from flask import Blueprint
from application.textController import uploadBlueprint
from application.textController import appBlueprint


app = Flask(__name__)
# register routes from urls
app.register_blueprint(appBlueprint)
# we can register routes with specific prefix
app.register_blueprint(uploadBlueprint, url_prefix='/upload')
CORS(app)


if __name__ == '__main__':
    print("La aplicación se está ejecutando")
    app.run(debug=True, port=8080)
