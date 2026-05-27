import os
import pandas as pd
import tensorflow as tf
import pickle
from sklearn.model_selection import train_test_split
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.losses import MeanAbsoluteError

from src.models.custom_model import build_custom_model
from src.preprocessing import preprocess_data, clean_text, process_images

# --- Constants ---
MODEL_PATH = 'outputs/custom_multimodal_model.h5'
TOKENIZER_PATH = 'outputs/tokenizer.pkl'
TRAIN_CSV_PATH = 'dataset/train.csv'
IMAGE_DIR = 'dataset/images_train'
MAX_LEN = 128
VOCAB_SIZE = 10000

def smape(y_true, y_pred):
    y_true = tf.cast(y_true, tf.float32)
    y_pred = tf.cast(y_pred, tf.float32)
    numerator = tf.abs(y_pred - y_true)
    denominator = (tf.abs(y_true) + tf.abs(y_pred)) / 2.0 + tf.keras.backend.epsilon()
    return tf.reduce_mean(numerator / denominator) * 100

def main():
    # --- Load Data ---
    print("Loading data...")
    df = pd.read_csv(TRAIN_CSV_PATH).head(6000)

    # --- Load Tokenizer ---
    print("Loading tokenizer...")
    with open(TOKENIZER_PATH, 'rb') as handle:
        tokenizer = pickle.load(handle)

    # --- Preprocess Data ---
    print("Preprocessing data...")
    [text_data, image_data], labels, _ = preprocess_data(df, MAX_LEN, IMAGE_DIR, VOCAB_SIZE)
    
    # Split data
    _, X_val_text, \
    _, X_val_images, \
    _, y_val = train_test_split(text_data, image_data.numpy(), labels, test_size=0.2, random_state=42)

    # --- Load Model ---
    print("Loading model...")
    model = tf.keras.models.load_model(
        MODEL_PATH, 
        custom_objects={'smape': smape, 'mae': MeanAbsoluteError()}
    )

    # --- Evaluate Model ---
    print("Evaluating model...")
    results = model.evaluate([X_val_text, X_val_images], y_val)
    print(f"Validation Loss: {results[0]}")
    print(f"Validation SMAPE: {results[1]}")

if __name__ == '__main__':
    main()
