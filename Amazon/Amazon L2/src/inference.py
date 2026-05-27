import os
import pandas as pd
import tensorflow as tf
import pickle
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.losses import MeanAbsoluteError

from src.models.custom_model import build_custom_model
from src.preprocessing import clean_text, process_images

# --- Constants ---
MODEL_PATH = 'outputs/custom_multimodal_model.h5'
TOKENIZER_PATH = 'outputs/tokenizer.pkl'
TEST_CSV_PATH = '../dataset/test.csv'
# IMAGE_DIR = '../images'
SUBMISSION_PATH = 'outputs/predictions/test_predictions.csv'
MAX_LEN = 128
IMAGE_SHAPE = (224, 224, 3)

def main():
    # --- Load Model and Tokenizer ---
    print("Loading model and tokenizer...")
    model = tf.keras.models.load_model(
        MODEL_PATH, 
        custom_objects={'smape': smape, 'mae': MeanAbsoluteError()}
    )
    with open(TOKENIZER_PATH, 'rb') as handle:
        tokenizer = pickle.load(handle)

    # --- Load Test Data ---
    print("Loading test data...")
    df = pd.read_csv(TEST_CSV_PATH).head(1000)

    # --- Preprocess Test Data ---
    print("Preprocessing test data...")
    # Text data
    cleaned_texts = [clean_text(text) for text in df['catalog_content']]
    sequences = tokenizer.texts_to_sequences(cleaned_texts)
    text_data = pad_sequences(sequences, maxlen=MAX_LEN, padding='post', truncating='post')

    # Image data
    # First, we need to download the test images
    print("Downloading test images...")
    from src import utils
    utils.download_images(df['image_link'].tolist(), IMAGE_DIR)
    print("Test images downloaded.")
    
    image_data = process_images(df, IMAGE_DIR)

    # --- Make Predictions ---
    print("Making predictions...")
    predictions = model.predict([text_data, image_data])

    # --- Create Submission File ---
    print("Creating submission file...")
    submission = pd.DataFrame({
        'sample_id': df['sample_id'],
        'price': predictions.squeeze().clip(0)
    })
    submission.to_csv(SUBMISSION_PATH, index=False)
    print(f"Submission file saved to {SUBMISSION_PATH}")

def smape(y_true, y_pred):
    y_true = tf.cast(y_true, tf.float32)
    y_pred = tf.cast(y_pred, tf.float32)
    numerator = tf.abs(y_pred - y_true)
    denominator = (tf.abs(y_true) + tf.abs(y_pred)) / 2.0 + tf.keras.backend.epsilon()
    return tf.reduce_mean(numerator / denominator) * 100

if __name__ == '__main__':
    main()
