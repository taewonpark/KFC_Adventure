import re
import json
import torch

import random
import pandas as pd
from tqdm import tqdm
from simplet5 import SimpleT5
from torch.utils.data import Dataset
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split

from glob import glob
import shutil

import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Data load function
def load_sentiment_dataset(random_seed = 1, file_path="milestone0/data/training.1600000.processed.noemoticon.csv"):
    # load dataset and sample 10k reviews.
    df = pd.read_csv(file_path, encoding='ISO-8859-1', header=None)
    df = df[[0, 5]]
    df.columns = ['label', 'text']
    df = df.sample(int(len(df)*0.1), random_state=1) # 160000 samples 

    def pick_first_n_words(string, max_words=250): # tried a few max_words, kept 250 as max tokens was < 512
        split_str = string.split()
        return " ".join(split_str[:min(len(split_str), max_words)])

    df['text'] = df['text'].apply(lambda x: pick_first_n_words(x))
    map_label = {0:'negative', 4: 'positive'}
    df['label'] = df['label'].apply(lambda x: map_label[x])

    # divide into test and train
    X_train, X_test, y_train, y_test = \
              train_test_split(df['text'].tolist(), df['label'].tolist(),
              shuffle=True, test_size=0.2, random_state=random_seed, stratify=df['label'])

    X_train, X_val, y_train, y_val = \
              train_test_split(X_train, y_train, 
              shuffle=True, test_size=0.25, random_state=random_seed, stratify=y_train) # 0.25 x 0.8 = 0.2

    # transform to pandas dataframe
    train_data = pd.DataFrame({'source_text': X_train, 'target_text': y_train})
    val_data = pd.DataFrame({'source_text': X_val, 'target_text': y_val})
    test_data = pd.DataFrame({'source_text': X_test, 'target_text': y_test})

    print("number of train, val, test: ", len(X_train), len(X_val), len(X_test))

    return train_data, val_data, test_data

for trial_no in range(1):
    # create data
    train_df, val_df, test_df = load_sentiment_dataset(trial_no)
    # load model
    model = SimpleT5()
    model.from_pretrained(model_type="t5", model_name="t5-base")
    
    # # train model
    model.train(train_df=train_df,
                eval_df=val_df,
                source_max_token_len=300,
                target_max_token_len=200,
                batch_size=8,
                max_epochs=2,
                outputdir = "outputs",
                dataloader_num_workers=24,
                use_gpu=True,
              )
    
    # fetch the path to last model
    last_epoch_model = None
    for file in glob("./outputs/*"):
        if 'epoch-1' in file:
            last_epoch_model = file

    # load the last model
    print('last_epoch_model', last_epoch_model)
    model.load_model("t5", last_epoch_model, use_gpu=True)
    
    # test and save
    # for each test data perform prediction
    predictions = []
    for index, row in test_df.iterrows():
        prediction = model.predict(row['source_text'])[0]
        predictions.append(prediction)
    df = test_df.copy()
    df['predicted'] = predictions
    df['original'] = df['target_text']
    print("f1_score", f1_score(df['original'], df['predicted'], average='macro'))
    
    df.to_csv(f"result_run_{trial_no}.csv", index=True)


"""
Global seed set to 42
number of train, val, test:  96000 32000 32000
GPU available: True, used: True
TPU available: False, using: 0 TPU cores
IPU available: False, using: 0 IPUs

  | Name  | Type                       | Params
-----------------------------------------------------
0 | model | T5ForConditionalGeneration | 222 M 
-----------------------------------------------------
222 M     Trainable params
0         Non-trainable params
222 M     Total params
891.614   Total estimated model params size (MB)
Global seed set to 42                                                 
Epoch 1: 100%|██████████| 16000/16000 [1:21:19<00:00,  3.28it/s, loss=0.147, v_num=7, train_loss_step=0.129, val_loss_step=0.120, val_loss_epoch=0.171, train_loss_epoch=0.151]  
last_epoch_model ./outputs/simplet5-epoch-1-train-loss-0.151-val-loss-0.1711
f1_score 0.8552054231014862   
"""