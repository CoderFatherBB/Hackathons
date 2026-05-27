import os
import pandas as pd
import tensorflow as tf
from sklearn.model_selection import train_test_split
import pickle

from models.custom_model import build_custom_model
from preprocessing import preprocess_data

# --- Constants ---
MAX_LEN = 128
VOCAB_SIZE = 10000
EMBEDDING_DIM = 128
IMAGE_SHAPE = (224, 224, 3)
BATCH_SIZE = 32
EPOCHS = 10
MODEL_PATH = 'outputs/custom_multimodal_model.h5'
TOKENIZER_PATH = 'outputs/tokenizer.pkl'
TRAIN_CSV_PATH = 'dataset/train.csv'
IMAGE_DIR = 'images/train'

# --- Custom SMAPE Metric ---
def smape(y_true, y_pred):
    y_true = tf.cast(y_true, tf.float32)
    y_pred = tf.cast(y_pred, tf.float32)
    numerator = tf.abs(y_pred - y_true)
    denominator = (tf.abs(y_true) + tf.abs(y_pred)) / 2.0 + tf.keras.backend.epsilon()
    return tf.reduce_mean(numerator / denominator) * 100

def main():
    # --- Load Data ---
    print("Loading data...")
    df = pd.read_csv(TRAIN_CSV_PATH)

    # --- Preprocess Data ---
    print("Preprocessing data...")
    [text_data, image_data], labels, tokenizer = preprocess_data(df, MAX_LEN, IMAGE_DIR, VOCAB_SIZE)
    
    # Save the tokenizer
    with open(TOKENIZER_PATH, 'wb') as handle:
        pickle.dump(tokenizer, handle, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"Tokenizer saved to {TOKENIZER_PATH}")

    # Split data
    X_train_text, X_val_text, \
    X_train_images, X_val_images, \
    y_train, y_val = train_test_split(text_data, image_data.numpy(), labels, test_size=0.2, random_state=42)

    # --- Build Model ---
    print("Building model...")
    model = build_custom_model(VOCAB_SIZE, EMBEDDING_DIM, MAX_LEN, IMAGE_SHAPE)

    # --- Compile Model ---
    print("Compiling model...")
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
                  loss='mae',
                  metrics=[smape])
    
    model.summary()

    # --- Callbacks ---
    checkpoint = tf.keras.callbacks.ModelCheckpoint(
        filepath=MODEL_PATH,
        monitor='val_loss',
        save_best_only=True,
        save_weights_only=False,
        verbose=1
    )
    early_stopping = tf.keras.callbacks.EarlyStopping(
        monitor='val_loss',
        patience=3,
        restore_best_weights=True,
        verbose=1
    )

    # --- Train Model ---
    print("Training model...")
    history = model.fit(
        [X_train_text, X_train_images],
        y_train,
        validation_data=([X_val_text, X_val_images], y_val),
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        callbacks=[checkpoint, early_stopping]
    )

    print("Training complete.")
    print(f"Model saved to {MODEL_PATH}")

if __name__ == '__main__':
    main()
