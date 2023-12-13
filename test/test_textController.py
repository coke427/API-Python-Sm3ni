import pytest
from flask import Flask
from flask.testing import FlaskClient
from io import BytesIO
from application.textController import uploadBlueprint

@pytest.fixture
def app():
    # Crea una aplicación Flask simple para las pruebas
    app = Flask(__name__)
    app.register_blueprint(uploadBlueprint)

    return app

@pytest.fixture
def client(app):
    # Crea un cliente de prueba para la aplicación Flask
    return app.test_client()

def test_upload_file(client: FlaskClient):
    # Ruta de la imagen de prueba
    image_path = 'test/ex2.png'
    
    # Lee la imagen en formato binario
    with open(image_path, 'rb') as image_file:
        image_content = image_file.read()

    # Realiza la solicitud POST
    response = client.post('/', data={'file': (BytesIO(image_content), 'test.jpg')})

    # Verifica que la respuesta tenga el formato correcto y la carga del archivo fue exitosa
    assert response.status_code == 200, f"La carga del archivo falló. Código de estado: {response.status_code}"
    assert 'message' in response.json, "La respuesta no contiene la clave 'message'"
    assert 'staff_lines' in response.json, "La respuesta no contiene la clave 'staff_lines'"
    assert 'symbols' in response.json, "La respuesta no contiene la clave 'symbols'"