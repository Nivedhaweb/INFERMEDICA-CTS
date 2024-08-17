from flask import Flask, jsonify, request, make_response, render_template
from pymongo import MongoClient
import pdfkit

# Specify the path to the wkhtmltopdf executable
path_to_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
config = pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf)
css_path = 'styles.css'

app = Flask(__name__)

client = MongoClient('mongodb://localhost:27017/')
db = client['myDb']
collection = db['patients']


def generate_description(data_list):
    descriptions = []

    for data in data_list:
        description = "<html><body>"

        # Basic Information
        description += f"<h2>Patient ID: {data['id']}</h2>"
        description += f"<p><strong>Name:</strong> {data['name']['first']} {data['name']['last']}</p>"
        description += f"<p><strong>Date of Birth:</strong> {data['dob']}</p>"

        # Medical History
        medical_history = data['medical_history']
        description += "<p><strong>Medical History:</strong></p>"

        # Unique Allergies
        if 'allergies' in medical_history:
            unique_allergies = set(medical_history['allergies'])  # Use a set to remove duplicates
            description += f"<p>  Allergies: {', '.join(unique_allergies)}</p>"

        if 'conditions' in medical_history and len(medical_history['conditions']) > 0:
            description += "<p>  Conditions:</p>"
            for condition in medical_history['conditions']:
                description += f"<p>    - {condition['name']} (Diagnosed on: {condition['diagnosed_date']}, Status: {condition['status']})</p>"

        if 'surgeries' in medical_history and len(medical_history['surgeries']) > 0:
            description += "<p>  Surgeries:</p>"
            for surgery in medical_history['surgeries']:
                description += f"<p>    - {surgery['name']} (Date: {surgery['date']}, Outcome: {surgery['outcome']})</p>"

        if 'medications' in medical_history and len(medical_history['medications']) > 0:
            description += "<p>  Medications:</p>"
            for medication in medical_history['medications']:
                description += f"<p>    - {medication['name']} (Dose: {medication['dose']}, Frequency: {medication['frequency']}, Start Date: {medication['start_date']})</p>"

        description += "</body></html>"

        descriptions.append(description)

    return "\n\n".join(descriptions)


@app.route('/', methods=['GET', 'POST'])
def home():
    patient_description = ""
    if request.method == 'POST':
        doctor_name = request.form['doctor_name']
        patient_data_list = list(collection.find({"appointments.doctor.name": doctor_name}))

        if patient_data_list:
            patient_description = generate_description(patient_data_list)
        else:
            patient_description = "No patients found for the specified doctor."

    return render_template('index.html', description=patient_description)


@app.route('/download_pdf', methods=['POST'])
def download_pdf():
    description = request.form['description']

    # Generate PDF
    pdf = pdfkit.from_string(description, False, configuration=config, css=css_path)

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=patient_data.pdf'
    return response


if __name__ == '__main__':
    app.run(debug=True)
