from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint
from application.textController import uploadBlueprint
from application.textController import appBlueprint

app = Flask(__name__)

SWAGGER_URL = '/swagger'
API_URL = '/static/swagger.json'  # Ruta donde se encuentra tu archivo swagger.json

# Configuración para Flask-Swagger-UI
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Tu Aplicación Flask"
    }
)

# Registrar la ruta de la interfaz Swagger en tu aplicación
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# register routes from urls
app.register_blueprint(appBlueprint)
# we can register routes with specific prefix
app.register_blueprint(uploadBlueprint, url_prefix='/upload')
CORS(app)

if __name__ == '__main__':
    print("La aplicación se está ejecutando")
    app.run(host='0.0.0.0', debug=True, port=8080)

