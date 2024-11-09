# Wildfire Prediction and Visualization

## Overview

This project aims to predict wildfire occurrences using various environmental and meteorological data. The project includes data exploration, preprocessing, model training using Logistic Regression, and visualization of the results using a web dashboard.

## Project Structure


## Data Sources

- **Soil Data**: Contains various soil properties.
- **Fire Data**: Historical wildfire data.
- **Meteorological Data**: Weather conditions at different times.
- **Satellite Data**: NDVI data from VIIRS.

## Setup

1. **Clone the repository**:
    ```sh
    git clone <repository-url>
    cd <repository-directory>
    ```

2. **Install dependencies**:
    ```sh
    pip install -r requirements.txt
    ```

3. **Download additional data**:
    - Wildfire data: [Kaggle Dataset](https://www.kaggle.com/datasets/rtatman/188-million-us-wildfires)
    - FIPS data: [Statalist](https://www.statalist.org/forums/forum/general-stata-discussion/general/1399818-converting-geo-coordinates-to-fips-codes)

## Usage

### Data Exploration

Open [`data_exploration.ipynb`](data_exploration.ipynb) to explore and preprocess the data. This notebook includes steps for loading data, creating features, and visualizing the data.

### Model Training

The model training is performed in [`data_exploration.ipynb`](data_exploration.ipynb). The code snippet below shows the Logistic Regression model setup:

```python
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

X_train, X_test, y_train, y_test = train_test_split(df[ALL_FEATURES], df[TARGET], test_size=0.2, random_state=42)

model = LogisticRegression()
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f'Accuracy: {accuracy}')
```

### Dashboard
Run dashboard.py to start the web dashboard for visualizing the wildfire predictions:

```python
python [dashboard.py]
```

The dashboard includes a map with wildfire markers and a date range slider to filter the data.

## Contributing
Fork the repository.
Create a new branch (git checkout -b feature-branch).
Commit your changes (git commit -am 'Add new feature').
Push to the branch (git push origin feature-branch).
Create a new Pull Request.
License
This project is licensed under the MIT License.

## Acknowledgements
Kaggle for the wildfire dataset.
Statalist for the FIPS data conversion guide.
Folium for the mapping library.
Scikit-learn for the machine learning framework.