from transformers import MarianMTModel, MarianTokenizer

# Define models for different language pairs
models = {
    'en-es': 'Helsinki-NLP/opus-mt-en-es',  # English to Spanish
    'es-en': 'Helsinki-NLP/opus-mt-es-en',  # Spanish to English
    'en-fr': 'Helsinki-NLP/opus-mt-en-fr',  # English to French
    'fr-en': 'Helsinki-NLP/opus-mt-fr-en',  # French to English
    'en-de': 'Helsinki-NLP/opus-mt-en-de',  # English to German
    'de-en': 'Helsinki-NLP/opus-mt-de-en',  # German to English
    'en-zh': 'Helsinki-NLP/opus-mt-en-zh',  # English to Chinese
    'zh-en': 'Helsinki-NLP/opus-mt-zh-en',  # Chinese to English
}

def download_models():
    for language_pair, model_name in models.items():
        print(f"Downloading model for {language_pair}...")
        tokenizer = MarianTokenizer.from_pretrained(model_name)
        model = MarianMTModel.from_pretrained(model_name)
        print(f"Model for {language_pair} downloaded successfully.")

if __name__ == "__main__":
    download_models()
