import pandas as pd
from flask import Flask, render_template, request
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import pickle

# Load the datasets
df_training = pd.read_csv('Training.csv')
df_testing = pd.read_csv('Testing.csv')
df_severity = pd.read_csv('symptom_severity.csv')
df_precaution = pd.read_csv('disease_precaution.csv')
df_description = pd.read_csv('disease_description.csv')
df_symptoms = pd.read_csv('newDataset.csv')
df_treatment = pd.read_csv('treatment.csv')

# Merge the datasets
df_merged = pd.merge(df_symptoms, df_description, on='Disease')
df_merged = pd.merge(df_merged, df_precaution, on='Disease')
df_merged = pd.merge(df_merged, df_treatment, on='Disease')

# Preprocess the data
symptom_columns = df_merged.columns[1:-2]  # Exclude 'Disease', 'Description', and 'Treatment' columns
df_merged['Combined_Symptoms'] = df_merged[symptom_columns].apply(lambda x: ','.join(x.dropna()), axis=1)

# Preprocess the text data
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(df_merged['Combined_Symptoms'])
y = df_merged['Disease']

# Train the model
model = LogisticRegression()
model.fit(X, y)

# Save the model
pickle.dump(model, open('model.pkl', 'wb'))

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    # Get the input symptoms from the user
    user_input = [request.form['symptoms']]

    # Preprocess the user input
    user_input_vector = vectorizer.transform(user_input)

    # Make the prediction using the trained model
    predicted_probabilities = model.predict_proba(user_input_vector)[0]
    
    # Get the predicted diseases and their probabilities
    diseases = model.classes_
    probabilities = predicted_probabilities.tolist()

    # Create a list of dictionaries with disease, probability, description, precautions, and treatment information
    results = []
    for disease, probability in zip(diseases, probabilities):
        disease_description = df_merged[df_merged['Disease'] == disease]['Description'].values[0]
        disease_precautions = df_merged[df_merged['Disease'] == disease][
            ['Precaution_1', 'Precaution_2', 'Precaution_3', 'Precaution_4']].values[0]
        disease_treatment = df_merged[df_merged['Disease'] == disease]['Treatment'].values[0]
        
        results.append({
            'disease': disease,
            'probability_range': f'{probability*100:.2f}%',
            'description': disease_description,
            'precautions': disease_precautions,
            'treatment': disease_treatment
        })

    # Sort the results by probability in descending order
    results.sort(key=lambda x: x['probability_range'], reverse=True)

    # Get the top 3 diseases with highest probabilities
    top_results = results[:3]

    # Check if any data exists in the top results list
    if not top_results:
        return render_template('index.html', error='Please enter valid symptoms.')

    return render_template('result.html', results=top_results)

@app.route('/news-detail')
def news1():
    return render_template('news-detail.html')

if __name__ == '__main__':
    app.run(debug=True)
