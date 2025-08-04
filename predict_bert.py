from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification
import torch

# Load model/tokenizer
model = DistilBertForSequenceClassification.from_pretrained("./bert_model")
tokenizer = DistilBertTokenizerFast.from_pretrained("./bert_tokenizer")
model.eval()

# FUNCTION to predict news
def predict_news(text):
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    probs = torch.nn.functional.softmax(outputs.logits, dim=1)
    confidence = float(probs.max()) * 100
    prediction = torch.argmax(probs, dim=1).item()
    label = "REAL ✅" if prediction == 1 else "FAKE ❌"
    return label, round(confidence, 2)

# 🧪 Test
if __name__ == "__main__":
    text = input("📰 Enter a news headline: ")
    label, confidence = predict_news(text)
    print(f"\nPrediction: {label}")
    print(f"Confidence: {confidence}%")
