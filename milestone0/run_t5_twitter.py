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

# Data load function
def load_sentiment_dataset(random_seed = 1, file_path="training.1600000.processed.noemoticon.csv"):
    # load dataset and sample 10k reviews.
    df = pd.read_csv(file_path, encoding='ISO-8859-1', header=None)
    df = df[[0, 5]]
    df.columns = ['label', 'text']
    df = df.sample(10000, random_state=1)

    def pick_first_n_words(string, max_words=250): # tried a few max_words, kept 250 as max tokens was < 512
        split_str = string.split()
        return " ".join(split_str[:min(len(split_str), max_words)])

    df['text'] = df['text'].apply(lambda x: pick_first_n_words(x))
    map_label = {0:'negative', 4: 'positive'}
    df['label'] = df['label'].apply(lambda x: map_label[x])

    # divide into test and train
    X_train, X_test, y_train, y_test = \
              train_test_split(df['text'].tolist(), df['label'].tolist(),
              shuffle=True, test_size=0.05, random_state=random_seed, stratify=df['label'])

    # transform to pandas dataframe
    train_data = pd.DataFrame({'source_text': X_train, 'target_text': y_train})
    test_data = pd.DataFrame({'source_text': X_test, 'target_text': y_test})

    # return
    return train_data, test_data

from glob import glob
import shutil

for trial_no in range(1):
    # create data
    train_df, test_df = load_sentiment_dataset(trial_no)
    # load model
    model = SimpleT5()
    model.from_pretrained(model_type="t5", model_name="t5-base")
    # train model
    model.train(train_df=train_df,
                eval_df=test_df,
                source_max_token_len=300,
                target_max_token_len=200,
                batch_size=8,
                max_epochs=2,
                outputdir = "outputs",
                use_gpu=True
               )
    # fetch the path to last model
    last_epoch_model = None
    for file in glob("./outputs/*"):
        if 'epoch-1' in file:
            last_epoch_model = file
    # load the last model
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
    print(f1_score(df['original'], df['predicted'], average='macro'))
    df.to_csv(f"result_run_{trial_no}.csv", index=False)
    # clean the output
    shutil.rmtree("outputs")


"""
Global seed set to 42
/home/taewon/anaconda3/envs/qg/lib/python3.7/site-packages/transformers/models/t5/tokenization_t5_fast.py:165: FutureWarning: This tokenizer was incorrectly instantiated with a model max length of 512 which will be corrected in Transformers v5.
For now, this behavior is kept to avoid breaking backwards compatibility when padding/encoding with `truncation is True`.
- Be aware that you SHOULD NOT rely on t5-base automatically truncating your input to 512 when padding/encoding.
- If you want to encode/pad to sequences longer than 512 you can either instantiate this tokenizer with `model_max_length` or pass `max_length` when encoding/padding.
- To avoid this warning, please instantiate this tokenizer with `model_max_length` set to your preferred value.
  FutureWarning,
GPU available: True, used: True
TPU available: False, using: 0 TPU cores
IPU available: False, using: 0 IPUs
LOCAL_RANK: 0 - CUDA_VISIBLE_DEVICES: [1]

  | Name  | Type                       | Params
-----------------------------------------------------
0 | model | T5ForConditionalGeneration | 222 M 
-----------------------------------------------------
222 M     Trainable params
0         Non-trainable params
222 M     Total params
891.614   Total estimated model params size (MB)
Validation sanity check: 0it [00:00, ?it/s]/home/taewon/anaconda3/envs/qg/lib/python3.7/site-packages/pytorch_lightning/trainer/data_loading.py:133: UserWarning: The dataloader, val_dataloader 0, does not have many workers which may be a bottleneck. Consider increasing the value of the `num_workers` argument` (try 40 which is the number of cpus on this machine) in the `DataLoader` init to improve performance.
  f"The dataloader, {name}, does not have many workers which may be a bottleneck."
Global seed set to 42                                                                                                                   
/home/taewon/anaconda3/envs/qg/lib/python3.7/site-packages/pytorch_lightning/trainer/data_loading.py:133: UserWarning: The dataloader, train_dataloader, does not have many workers which may be a bottleneck. Consider increasing the value of the `num_workers` argument` (try 40 which is the number of cpus on this machine) in the `DataLoader` init to improve performance.
  f"The dataloader, {name}, does not have many workers which may be a bottleneck."
Epoch 1: 100%|█| 1251/1251 [06:55<00:00,  3.01it/s, loss=0.163, v_num=5, train_loss_step=0.038, val_loss_step=0.305, val_loss_epoch=0.18
0.8418931197489503   
"""