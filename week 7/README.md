# Clickbait Headline Detector

This project fine tunes distilbert-base-uncased on christinacdl/clickbait_detection_dataset
(37.9k labeled headlines) to classify headlines as clickbait or genuine.


## Files

- config.py - shared constants (dataset name, label maps, hyperparameters, paths)
- train.py - fine-tunes DistilBERT and saves the model to clickbait-distilbert/
- predict.py - ClickbaitPredictor class for loading the model and running inference
- app.py - Streamlit UI for single-headline and batch (CSV) predictions
- clickbait_detector.ipynb - all-in-one notebook version (setup, training, evaluation, interactive UI)
- requirements.txt - pinned dependencies


## Setup

```bash
python -m venv venv
source venv\Scripts\activate    
pip install -r requirements.txt
```


## Train the model

```bash
python train.py
```

Optional flags:

```bash
python train.py --epochs 4 --batch-size 16 --lr 3e-5
```

This will:

1. Download and split christinacdl/clickbait_detection_dataset (train/val/test)
2. Tokenize headlines with the DistilBERT tokenizer
3. Fine-tune with early stopping on validation F1
4. Report test-set accuracy, precision, recall, F1, macro F1
5. Save the model and tokenizer to clickbait-distilbert/


## Run predictions from the command line

```bash
python predict.py "You Won't Believe What Happened Next"
```

---

## Launch the UI

```bash
streamlit run app.py
```

The UI expects a fine-tuned model already saved at clickbait-distilbert/
(i.e. run train.py first). It supports:

- Single headline check with class probabilities
- Batch scoring from an uploaded CSV, with a downloadable results file

