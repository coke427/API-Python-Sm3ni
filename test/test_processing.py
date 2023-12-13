import pytest
import numpy as np
import base64
from domain.service.preprocessing.preprocessing import preprocessing_from_base64

def read_base64_from_file():
    try:
        with open('test/imagen_codificada.txt', 'r') as file:
            base64_str = file.read().strip()
        base64_bytes = base64.b64decode(base64_str)
        return base64_bytes
    except Exception as e:
        pytest.fail(f"Error al leer o decodificar la imagen base64: {str(e)}")

@pytest.mark.only
def test_preprocessing_from_base64():
    try:
        base64_image = read_base64_from_file()
        result = preprocessing_from_base64(base64_image)
        assert isinstance(result, np.ndarray)
        assert result.shape[0] > 100 and result.shape[1] > 100, "La imagen tiene dimensiones mayores a 100 píxeles."
    except Exception as e:
        pytest.fail(f"Error en la prueba: {str(e)}")
