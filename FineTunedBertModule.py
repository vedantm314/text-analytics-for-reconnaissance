from transformers import Trainer 
from transformers import BertTokenizerFast
from transformers import BertForSequenceClassification
import numpy as np
import pandas as pd

class FineTunedBertModule: 
    category_array = ["buildings", "infrastructure ", "other", "resilience"] 
    
    def __init__(self): 
        self.model = BertForSequenceClassification.from_pretrained("fineTunedBert")
        self.tokenizer = BertTokenizerFast.from_pretrained("bert-base-uncased")
    
    def tokenize_sentence(self, sentence):
        return self.tokenizer(sentence, padding="max_length", truncation=True, return_tensors="pt")

    def get_predictions(self, sentences):
        preds = []

        for x in range(0, len(sentences)): 

            tokenized_sentence = self.tokenize_sentence(sentences[x])

            logits = self.model(**tokenized_sentence).logits


            numerical_prediction = np.argmax(logits.detach().numpy(), axis = -1)

            preds.append(numerical_prediction[0])
            
        preds = list(map(lambda x: self.category_array[x], preds))
        
        sentences_with_preds = {"sentence": sentences, "label": preds}

        df = pd.DataFrame.from_dict(sentences_with_preds)

        return df
        
        