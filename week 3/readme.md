# Week 3 - NLP and Text Classification

This covers the tasks assigned for Week 3 focused on NLP and text classification.

## Topics Covered

### 1. Basic ML Workflow
Covers the general pipeline used in any ML project: dataset, features, labels, train/test split, model training, prediction, evaluation, and the concepts of overfitting and underfitting. Demonstrated using the Iris dataset with a Decision Tree classifier.

### 2. Text Classification
Covers what text classification is, along with common real-world examples: sentiment classification, legal topic classification, news category classification, complaint classification, and spam detection.

### 3. NLP Preprocessing
Covers the basic steps used to clean text before it can be used in a model: lowercasing, removing punctuation, stop word removal, tokenization, and the basic idea behind stemming vs lemmatization. Demonstrated using a sample review from the IMDB dataset.

### 4. Text Vectorization
Covers how raw text is converted into numerical features: Bag of Words, TF-IDF, an introduction to embeddings, and the difference between TF-IDF and embeddings. Demonstrated using sample movie reviews, the full IMDB dataset (TF-IDF), and a pretrained GloVe model (embeddings).

### 5. ML Models for Text
Covers four models trained and evaluated on different datasets:
- **Logistic Regression** - IMDB Dataset (binary sentiment classification)
- **Naive Bayes** - SMS Spam Collection Dataset (binary, imbalanced)
- **Random Forest** - Spam dataset and BBC News dataset (multi-class)
- **Support Vector Machine (SVM)** - 20 Newsgroups dataset (multi-class)

### 6. Evaluation
Covers accuracy, precision, recall, F1 score, and confusion matrix, along with how these metrics behave differently across balanced vs. imbalanced datasets and binary vs. multi-class problems. Applied to each of the four models above.

## Datasets Used
- Iris dataset (built into scikit-learn)
- IMDB Dataset of 50K Movie Reviews (Kaggle)
- SMS Spam Collection Dataset (Kaggle)
- SetFit/bbc-news (Hugging Face)
- 20 Newsgroups (built into scikit-learn)

## Tools/Libraries Used
- pandas, scikit-learn, nltk, gensim, matplotlib