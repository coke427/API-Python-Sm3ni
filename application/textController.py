from flask import Blueprint, jsonify, request

from domain.service.preprocessing.preprocessing import preprocessing_from_base64
from domain.service.text import process_image

appBlueprint = Blueprint('app', __name__,)
@appBlueprint.route('/')
def index():
    return "Api Rest Coke Running"

uploadBlueprint = Blueprint('textController', __name__,)
@uploadBlueprint.route('/', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No se proporcionó ningún archivo'})

    file = request.files['file']

    if file.filename == '' or not file.filename.endswith(('.png', '.jpg', '.jpeg')):
        return jsonify({'error': 'Archivo no válido'})

    # Leer el contenido del archivo y cargarlo en una imagen
    file_contents = file.read()

    # Llama a la función preprocessing_from_base64 con los datos de la imagen en memoria
    binarizedImg = preprocessing_from_base64(file_contents)

    # Procesa la imagen utilizando el código original
    results = process_image(binarizedImg)

    # Retorna los resultados como un JSON
    return jsonify(results)