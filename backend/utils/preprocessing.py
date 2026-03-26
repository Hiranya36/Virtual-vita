import pandas as pd
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder


def load_and_preprocess():

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    dataset_path = os.path.join(base_dir, "backend", "dataset", "dataset.csv")

    data = pd.read_csv(dataset_path)

    print("Dataset loaded")

    # split symptom string into list
    data["symptoms"] = data["symptoms"].apply(lambda x: x.split(","))

    # build symptom vocabulary
    all_symptoms = set()

    for symptoms in data["symptoms"]:
        for s in symptoms:
            all_symptoms.add(s.strip())

    all_symptoms = sorted(list(all_symptoms))

    print("Total symptoms:", len(all_symptoms))

    # convert symptoms into binary vector
    X = []

    for symptoms in data["symptoms"]:

        vector = [0] * len(all_symptoms)

        for s in symptoms:
            if s.strip() in all_symptoms:
                idx = all_symptoms.index(s.strip())
                vector[idx] = 1

        X.append(vector)

    X = pd.DataFrame(X, columns=all_symptoms)

    y = data["disease"]

    # encode disease labels
    encoder = LabelEncoder()
    y_encoded = encoder.fit_transform(y)

    print("Encoded disease classes:", len(encoder.classes_))

    # split dataset
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42
    )

    print("Training samples:", X_train.shape)
    print("Testing samples:", X_test.shape)

    return X_train, X_test, y_train, y_test, encoder