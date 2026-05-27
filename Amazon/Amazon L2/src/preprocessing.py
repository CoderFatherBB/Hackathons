import re
import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from src import utils
import os
from tqdm import tqdm

def clean_text(text):
    """
    Cleans the input text by lowercasing it, and removing special characters.
    """
    if not isinstance(text, str):
        text = str(text)
    text = text.lower()
    text = re.sub(r'[^a-zA-Z0-9\s\.]', '', text)
    return text

def process_text(texts, max_len, num_words=10000):
    """
    Cleans and tokenizes a list of texts.
    """
    cleaned_texts = [clean_text(text) for text in texts]
    
    tokenizer = Tokenizer(num_words=num_words, oov_token="<unk>")
    tokenizer.fit_on_texts(cleaned_texts)
    
    sequences = tokenizer.texts_to_sequences(cleaned_texts)
    padded_sequences = pad_sequences(sequences, maxlen=max_len, padding='post', truncating='post')
    
    return padded_sequences, tokenizer

def load_and_preprocess_image(image_path, target_size=(224, 224)):
    """
    Loads an image from a given path, resizes it, and normalizes it.
    """
    try:
        img = tf.io.read_file(image_path)
        img = tf.image.decode_jpeg(img, channels=3)
        img = tf.image.resize(img, target_size)
        img = img / 255.0  # Normalize to [0,1]
        return img
    except Exception as e:
        print(f"Warning: Could not process image {image_path}. Error: {e}")
        return tf.zeros(target_size + (3,))


def process_images(df, image_folder, target_size=(224, 224)):
    """
    Loads and preprocesses images.
    """
    if 'image_link' not in df.columns:
        raise ValueError("DataFrame must have an 'image_link' column.")

    # Process images
    image_paths = [os.path.join(image_folder, os.path.basename(link)) for link in df['image_link']]
    
    processed_images = []
    for path in tqdm(image_paths, desc="Processing images"):
        if isinstance(path, str) and os.path.exists(path):
            processed_images.append(load_and_preprocess_image(path, target_size))
        else:
            # Handle cases where the link was invalid or download failed
            print(f"Warning: Image path not found {path}. Using a placeholder.")
            processed_images.append(tf.zeros(target_size + (3,)))

    return tf.stack(processed_images)

def preprocess_data(df, max_len, image_folder, num_words=10000):
    """
    Main function to preprocess both text and image data from a dataframe.
    """
    text_data, tokenizer = process_text(df['catalog_content'].tolist(), max_len, num_words)
    image_data = process_images(df, image_folder)
    
    if 'price' in df.columns:
        labels = df['price'].values
        return [text_data, image_data], labels, tokenizer
    else:
        return [text_data, image_data], tokenizer
