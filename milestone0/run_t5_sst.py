# reference url: https://www.kaggle.com/code/evilmage93/t5-finetuning-on-sentiment-classification/notebook
# !pip install datasets
# !pip install transformers
# !pip install simplet5

import pandas as pd
from simplet5 import SimpleT5
from sklearn.metrics import f1_score

from datasets import load_dataset


# load dataset
dataset = load_dataset('glue', 'sst2')
train_dataset = dataset['train']
valid_dataset = dataset['validation']
# test_dataset = dataset['test']

label_id2txt = {0: 'negative', 1: 'positive'}
train_df = pd.DataFrame({'source_text': train_dataset['sentence'], 'target_text': [label_id2txt[label] for label in train_dataset['label']]})
test_df = pd.DataFrame({'source_text': valid_dataset['sentence'], 'target_text': [label_id2txt[label] for label in valid_dataset['label']]})

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
df.to_csv(f"result_run_{0}.csv", index=False)


"""
/home/taewon/anaconda3/envs/qg/lib/python3.7/site-packages/transformers/models/t5/tokenization_t5_fast.py:165: FutureWarning: This tokenizer was incorrectly instantiated with a model max length of 512 which will be corrected in Transformers v5.
For now, this behavior is kept to avoid breaking backwards compatibility when padding/encoding with `truncation is True`.
- Be aware that you SHOULD NOT rely on t5-base automatically truncating your input to 512 when padding/encoding.
- If you want to encode/pad to sequences longer than 512 you can either instantiate this tokenizer with `model_max_length` or pass `max_length` when encoding/padding.
- To avoid this warning, please instantiate this tokenizer with `model_max_length` set to your preferred value.
  FutureWarning,
GPU available: True, used: True
TPU available: False, using: 0 TPU cores
IPU available: False, using: 0 IPUs
LOCAL_RANK: 0 - CUDA_VISIBLE_DEVICES: [0,1]

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
Epoch 0:   2%|█▏                                               | 30/1251 [06:10<4:11:04, 12.34s/it, loss=2.35, v_num=1, train_loss_step=0.550]
Epoch 1: 100%|█| 8528/8528 [46:26<00:00,  3.06it/s, loss=0.0778, v_num=2, train_loss_step=0.00202, val_loss_step=0.0607, val_loss_epoch=0.09790.9334690892252969 
"""