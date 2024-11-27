"""
Copyright 2024 Kyle Luoma

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


This is the training script for the SNAILS naturalness classifier.
Run as-is to reproduce the published SNAILS word naturalness classifier model.
"""

from transformers import AutoTokenizer, CanineForSequenceClassification, TrainingArguments, Trainer, DataCollatorWithPadding
import torch
import pandas as pd
import numpy as np
from datasets import load_dataset
from dataclasses import dataclass
from transformers.tokenization_utils_base import PreTrainedTokenizerBase, PaddingStrategy
from typing import Optional, Union
import evaluate
import tokenprocessing as tp
import optuna

id2label = {0: "N1", 1: "N2", 2: "N3"}
label2id = {"N1": 0, "N2": 1, "N3": 2}

# Split into train and test sets. Should only need to do this once.
# df = pd.read_csv("./manual-scoring/manual-scores.csv")
table_df = pd.read_excel(
    "./gold-data/consolidated-scores-5-9-2024-no_whitespace.xlsx",
    sheet_name = "distinct-table"
    )
table_df = table_df[['TABLE_NAME', 'FINAL_SCORE']].rename(
    columns={'TABLE_NAME':'text', "FINAL_SCORE":'category'}
)
col_df = pd.read_excel(
    "./schema-scores/consolidated-scores-7-18-2023-2-QAQC.xlsx",
    sheet_name = "distinct-column"
)
col_df = col_df[['COLUMN_NAME', 'FINAL_SCORE']].rename(
    columns={'COLUMN_NAME':'text', 'FINAL_SCORE':'category'}
)

df = pd.concat([table_df, col_df])

df['label'] = df.apply(
    lambda row: label2id[row.category],
    axis = 1
)

msk = np.random.rand(len(df)) < 0.6
train = df[msk]
train_lower = train.copy()
train_lower['text'] = train_lower.text.str.lower()
train_upper = train.copy()
train_upper['text'] = train_upper.text.str.upper()
test_validate = df[~msk]
train = pd.concat([train, train_upper, train_lower])
train = train.sample(frac=1)

dataset_dir = "./classifier-training-data/canine2-upperlower"

msk = np.random.rand(len(test_validate)) < 0.5
validation = test_validate[msk]
test = test_validate[~msk]
train.to_csv(f"{dataset_dir}/train.csv", index = False)
validation.to_csv(f"{dataset_dir}/validation.csv", index = False)
test.to_csv(f"{dataset_dir}/test.csv", index = False)

model_name = "canine-s"

tokenizer = AutoTokenizer.from_pretrained(f"google/{model_name}")
manual_scores = load_dataset(dataset_dir, "default")

print(manual_scores)


def optuna_hp_space(trial):
    return{
        "optim" : trial.suggest_categorical("optim", ["adamw_hf", "adafactor"])
        ,"learning_rate" : trial.suggest_float("learning_rate", 3e-5, 5e-5, log=True)
        ,"weight_decay" : trial.suggest_float("weight_decay", 0.005, 0.05)
        ,"per_device_train_batch_size" : trial.suggest_categorical("per_device_train_batch_size", [8,12,16,20,24,32])
        ,"per_device_eval_batch_size" : trial.suggest_categorical("per_device_eval_batch_size", [8,12,16,20,24,32])
    }
    
      

def preprocess_function_tags(token):
    text_tags = []
    for t in token["text"]:
        text_tags.append(
            t + tp.make_token_tag(t)
        )
    return tokenizer(text_tags, truncation=True)


def preprocess_function(token):
    return tokenizer(token["text"], truncation=True)


tokenized_manual_scores = manual_scores.map(preprocess_function_tags, batched = True)


data_collator = DataCollatorWithPadding(tokenizer=tokenizer)
    
accuracy = evaluate.load("accuracy")

def compute_metrics(eval_pred):
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis = 1)
    return accuracy.compute(predictions = predictions, references = labels)


def model_init(trial):
    return CanineForSequenceClassification.from_pretrained(
    "google/canine-s",
    num_labels=3,
    id2label=id2label,
    label2id=label2id
    )


model = CanineForSequenceClassification.from_pretrained(
    "google/canine-s",
    num_labels=3,
    id2label=id2label,
    label2id=label2id
    )

training_args = TrainingArguments(
    output_dir=f"./models/{model_name}-collection2-upperlower-sequence-tags-best-hyperparams",
    evaluation_strategy="epoch",
    optim="adamw_hf",
    save_strategy="epoch",
    load_best_model_at_end=True,
    learning_rate=4.910828967396573e-05, # Best so far is 4e-5
    per_device_train_batch_size=24, # models without bs label in name are size 16
    per_device_eval_batch_size=12, #12 yields best performance
    num_train_epochs=15,
    weight_decay=0.04168784348465411 # models without wd label are 0.01
)

print(tokenized_manual_scores)
# print(tokenized_manual_scores["train"]["labels"])

trainer = Trainer(
    model=None,
    model_init=model_init,
    args=training_args,
    train_dataset=tokenized_manual_scores["train"],
    eval_dataset=tokenized_manual_scores["validation"],
    tokenizer=tokenizer,
    data_collator=data_collator,
    compute_metrics=compute_metrics,
)

# best_trial = trainer.hyperparameter_search(
#     direction="maximize",
#     backend="optuna",
#     hp_space=optuna_hp_space,
#     n_trials=20
# )

trainer.train()
trainer.save_model()


