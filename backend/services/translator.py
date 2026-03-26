from googletrans import Translator

translator = Translator()

def detect_language(text):

    result = translator.detect(text)

    return result.lang


def translate_to_english(text):

    translated = translator.translate(text, dest="en")

    return translated.text


def translate_from_english(text, target_lang):

    translated = translator.translate(text, dest=target_lang)

    return translated.text