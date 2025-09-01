import pandas as pd
import torch
import re
import string
from sklearn.metrics import classification_report, accuracy_score
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification, Trainer, TrainingArguments
from datasets import Dataset
import os

# 🚀 Load LIAR dataset
def load_liar_split(path):
    df = pd.read_csv(path, sep='\t', header=None, names=[
        "id", "label", "statement", "subject", "speaker", "job", "state", "party",
        "barely_true", "false", "half_true", "mostly_true", "pants_on_fire", "venue"
    ])
    return df[["statement", "label"]]

# 🧹 Preprocess the statement text
def preprocess(text):
    text = str(text).lower()  # lowercase
    text = re.sub(r'\[.*?\]', '', text)  # remove [brackets]
    text = re.sub(r'https?://\S+|www\.\S+', '', text)  # remove links
    text = re.sub(r'<.*?>+', '', text)  # remove HTML tags
    text = re.sub(r'[%s]' % re.escape(string.punctuation), '', text)  # remove punctuation
    text = re.sub(r'\n', ' ', text)  # remove newline
    text = re.sub(r'\w*\d\w*', '', text)  # remove words with numbers
    text = re.sub(r'\s+', ' ', text).strip()  # remove extra spaces
    return text

# 🧾 Label mapping: 6-class → binary
label_map = {
    "false": 0,
    "pants-fire": 0,
    "barely-true": 0,
    "half-true": 1,
    "mostly-true": 1,
    "true": 1
}

# 📂 Load splits
train_df = load_liar_split("liar_dataset/train.tsv")
val_df = load_liar_split("liar_dataset/valid.tsv")
test_df = load_liar_split("liar_dataset/test.tsv")

# 🧼 Clean + map + preprocess
def clean_and_map(df):
    df = df[df["label"].isin(label_map.keys())]
    df["label"] = df["label"].map(label_map)
    df = df.rename(columns={"statement": "text"})
    df["text"] = df["text"].apply(preprocess)
    return df

train_df = clean_and_map(train_df)
val_df = clean_and_map(val_df)

# 🧠 Tokenization
tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")

train_enc = tokenizer(train_df["text"].tolist(), truncation=True, padding=True)
val_enc = tokenizer(val_df["text"].tolist(), truncation=True, padding=True)

train_dataset = Dataset.from_dict({
    "input_ids": train_enc["input_ids"],
    "attention_mask": train_enc["attention_mask"],
    "labels": train_df["label"].tolist()
})

val_dataset = Dataset.from_dict({
    "input_ids": val_enc["input_ids"],
    "attention_mask": val_enc["attention_mask"],
    "labels": val_df["label"].tolist()
})

# 🧠 Load Model
model = DistilBertForSequenceClassification.from_pretrained("distilbert-base-uncased", num_labels=2)

# ⚙️ Training arguments
training_args = TrainingArguments(
    output_dir="./bert_model",
    num_train_epochs=3,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=64,
    warmup_steps=500,
    weight_decay=0.01,
    logging_dir="./logs",
    logging_steps=10,
    eval_strategy="epoch",
    save_strategy="epoch"
)

# 🛠️ Trainer Setup
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    tokenizer=tokenizer,
)

# 🚀 Train
trainer.train()

# ✅ Evaluate
preds_output = trainer.predict(val_dataset)
preds = torch.argmax(torch.tensor(preds_output.predictions), axis=1)
acc = accuracy_score(val_df["label"].tolist(), preds)
print("✅ BERT Accuracy:", acc)
print(classification_report(val_df["label"].tolist(), preds))

# 💾 Save Model + Tokenizer
model.save_pretrained("./bert_model")
tokenizer.save_pretrained("./bert_tokenizer")
print("📦 Saved to: bert_model/ and bert_tokenizer/")

