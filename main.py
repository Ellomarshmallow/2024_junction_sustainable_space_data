import pandas as pd
import pandas as pd

import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
  
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

'''
This dataset includes only the year 2015 for the FIPS code 06023.
If you want to download more data, please refer to the build_dataset.py file.
'''

df = pd.read_csv("data/masterdata.csv")

FEATURES = ["WS10M_MIN", "WS10M_MAX", "WS50M_MIN", "WS50M_MAX", "T2M_MIN", "T2M_MAX", "PRECTOT"]
INDEX_COLUMNS = ["DATE", "FIPS"]

TARGET = ['FIRE']
FEATURES = [column for column in df.columns if column not in (INDEX_COLUMNS+TARGET)]

X_train, X_test, y_train, y_test = train_test_split(df[FEATURES], df[TARGET], test_size=0.2, random_state=42)

model = LogisticRegression()
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f'Accuracy: {accuracy}')