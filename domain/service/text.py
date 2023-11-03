from domain.service.preprocessing.preprocessing import preprocessing_from_base64
from domain.service.staffremoval.staffremoval import *
from domain.service.classifiers.digitsClassifier import *
from domain.service.classifiers.accedintalsClassifier import *
from domain.service.inout.generateOutput import *
from domain.service.features.checkScanned import *
from domain.service.features.extractfeatures import *
from domain.service.deskewing.deskewing import *
from domain.service.generatingaudio.generatingAudio import *
from PIL import Image
import pickle
import os
import cv2
import numpy as np
import base64
import io

# Cargar los modelos aquí, en el alcance global del archivo
digitsFileModel = 'instructure/models/digits_model.sav'
symbolsFileModel = 'instructure/models/symbols_model.sav'
accedintalsFileModel = 'instructure/models/accedintals_model.sav'

loaded_digits_model = pickle.load(open(digitsFileModel, 'rb'))
loaded_symbols_model = pickle.load(open(symbolsFileModel, 'rb'))
loaded_accedintals_model = pickle.load(open(accedintalsFileModel, 'rb'))

def process_image(binarizedImg):
    # Copia de la imagen binarizada
    binarizedImgCopy = np.copy(binarizedImg)
    maxLenStaffLines = binarizedImg.shape[1]

    heights = []
    isHorizontal = getHorizontalLines(binarizedImg)
    origImg = (binarizedImg * 255).astype("uint8")
    if isHorizontal:
        segContours, segContoursDim, maxSpace, checkNumList, segPeakMids, segWidths = staffRemoval(binarizedImg)
    else:
        segContours, segContoursDim, maxSpace, checkNumList, segPeakMids, segWidths, segAspects, widths, heights, Ys = staffRemovalNonHorizontal(binarizedImg)

    # Check if image is reversed
    isImageReversed = isReversed(segContoursDim, maxSpace, maxLenStaffLines, heights)
    if isImageReversed:
        rotatedImage = inter.rotate(binarizedImgCopy, 180, reshape=True, order=0)
        isHorizontal = getHorizontalLines(rotatedImage)
        origImg = (rotatedImage * 255).astype("uint8")
        if isHorizontal:
            segContours, segContoursDim, maxSpace, checkNumList, segPeakMids, segWidths = staffRemoval(rotatedImage)
        else:
            segContours, segContoursDim, maxSpace, checkNumList, segPeakMids, segWidths, segAspects, widths, heights, Ys = staffRemovalNonHorizontal(rotatedImage)

    # Crear una estructura de datos para almacenar los resultados
    results = {'staff_lines': [], 'symbols': []}

    for i, seg in enumerate(segContours):
        staff_lines = []
        symbols = []
        hasAccidental = False
        accidental = ""
        hasNum = sum(checkNumList[i]) > 0

        for j, image in enumerate(seg):
            if checkNumList[i][j] == 1:
                features = extractDigitsFeatures(image)
                result = loaded_digits_model.predict([features])
                c = result[0]
                nums = []
                if c == 'b':
                    nums.append(2)
                else:
                    nums.append(4)
                if len(nums) == 2:
                    lineOut = f'\meter<"{nums[0]}/{nums[1]}">'
                    staff_lines.append(lineOut)
                    hasNum = False
            else:
                if hasNum:
                    continue
                if isHorizontal:
                    features, Bblobs, Wblobs = extractFeatures(image, maxSpace)
                else:
                    features, Bblobs, Wblobs = extractFeatures(image, maxSpace, segAspects[i][j], widths[i][j], heights[i][j], Ys[i][j])

                if len(Bblobs) + len(Wblobs) > 0:
                    ClassifierVote = loaded_symbols_model.predict([features])[0]
                    if isHorizontal:
                        className, Notes, duration = NoteOut(ClassifierVote, Bblobs, Wblobs, segContoursDim[i][j][2], segContoursDim[i][j][0], segPeakMids[i], segWidths[i], origImg, j, 0)
                    else:
                        className, Notes, duration = NoteOut(ClassifierVote, Bblobs, Wblobs, segContoursDim[i][j][2], segContoursDim[i][j][0], segPeakMids[i][j], segWidths[i][j], origImg, j, maxSpace)

                    if hasAccidental:
                        lineOut = formatLine(className, Notes, duration, accidental)
                        symbols.append(lineOut)
                        hasAccidental = False
                    else:
                        lineOut = formatLine(className, Notes, duration, '')
                        symbols.append(lineOut)
                else:
                    hasAccidental = True
                    features = extractAccedintalsFeatures(image)
                    result = loaded_accedintals_model.predict([features])
                    accidental = getAccedintals(result)
                    if accidental == 'bar' and image.shape[0] / image.shape[1] < 1.1:
                        accidental = '.'
                    if accidental == 'clef' or accidental == 'bar' or image.shape[0] > 5 * maxSpace:
                        hasAccidental = False
                    elif accidental == '.' and image.shape[0] < 2 * image.shape[1]:
                        w = segContoursDim[i][j][1] - segContoursDim[i][j][0]
                        h = segContoursDim[i][j][3] - segContoursDim[i][j][2]
                        if h / w > 1.2 or h / w < 0.8:
                            hasAccidental = False
                        symbols.append(accidental)

        # Genera el audio y almacénalo en una variable
        #audio_data = generateAudioData()

        # Convierte los datos de audio en una cadena base64
        #audio_base64 = base64.b64encode(audio_data.getvalue()).decode('utf-8')

    results = {
        'message': 'Archivo procesado con éxito',
        'staff_lines': staff_lines,
        'symbols': symbols
        #'audio_base64': audio_base64  # Agregar el audio en formato base64 al JSON
    }

    return results


def generateAudioData(inputText):
    audio_data = generateAudio(inputText)

    # Convierte los datos de audio en una cadena base64
    audio_base64 = base64.b64encode(audio_data.getvalue()).decode('utf-8')

    return audio_base64