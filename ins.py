from flask import Flask, request, render_template, make_response
from pymongo import MongoClient
import pdfkit

app = Flask(__name__)

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["myDb"]
collection = db["patients"]

# Specify the path to the wkhtmltopdf executable
path_to_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
config = pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf)

def generate_description_by_claim_id(data_list):
    descriptions = []
    for data in data_list:
        description = "<html><body>"
        description += f"<h2>Patient ID: {data['id']}</h2>"
        description += f"<p><strong>Name:</strong> {data['name']['first']} {data['name']['last']}</p>"
        
        insurance = data['insurance']
        if 'claimed_insurance' in insurance and len(insurance['claimed_insurance']) > 0:
            description += "<p><strong>Claimed Insurance:</strong></p>"
            for claim in insurance['claimed_insurance']:
                description += f"<p><strong>Claim ID:</strong> {claim['claim_id']}</p>"
                description += f"<p><strong>Date:</strong> {claim['date']}</p>"
                description += f"<p><strong>Amount:</strong> {claim['amount']}</p>"
                description += f"<p><strong>Status:</strong> {claim['status']}</p>"

        description += "</body></html>"
        descriptions.append(description)
    
    return "\n\n".join(descriptions)

def generate_description_by_insurance_name(data_list):
    descriptions = []
    for data in data_list:
        description = "<html><body>"
        description += f"<h2>Patient ID: {data['id']}</h2>"
        description += f"<p><strong>Name:</strong> {data['name']['first']} {data['name']['last']}</p>"
        description += f"<p><strong>Age:</strong> {data['age']}</p>"
        
        insurance = data['insurance']
        description += f"<p><strong>Insurance Provider:</strong> {insurance['provider']}</p>"
        description += f"<p><strong>Policy Number:</strong> {insurance['policy_number']}</p>"
        description += f"<p><strong>Group Number:</strong> {insurance['group_number']}</p>"
        description += f"<p><strong>Policy Effective Date:</strong> {insurance['effective_date']}</p>"
        description += f"<p><strong>Policy Expiration Date:</strong> {insurance['expiration_date']}</p>"
        
        # Handle missing 'nominee' field
        nominee = insurance.get('nominee', {})
        nominee_name = nominee.get('name', 'NA')
        nominee_relationship = nominee.get('relationship', 'NA')
        nominee_contact = nominee.get('contact', 'NA')
        description += f"<p><strong>Nominee:</strong> {nominee_name} ({nominee_relationship}) - {nominee_contact}</p>"
        
        if 'claimed_insurance' in insurance and len(insurance['claimed_insurance']) > 0:
            description += "<p><strong>Claimed Insurance:</strong></p>"
            for claim in insurance['claimed_insurance']:
                description += f"<p>  - Claim ID: {claim['claim_id']}, Date: {claim['date']}, Amount: {claim['amount']}, Status: {claim['status']}</p>"
        
        description += "</body></html>"
        descriptions.append(description)
    
    return "\n\n".join(descriptions)


@app.route('/')
def index():
    return render_template('index-ins.html')

@app.route('/retrieve', methods=['POST'])
def retrieve_data():
    data = request.json
    search_by = data['search_by']
    input_value = data['insurance_name'] if search_by == 'insurance_name' else data['claim_id']
    
    if search_by == 'insurance_name':
        result = list(collection.find({"insurance.provider": input_value}))
        if result and isinstance(result[0], dict):
            description = generate_description_by_insurance_name(result)
        else:
            description = "No valid records found or data format is incorrect."
    else:
        result = list(collection.find({"insurance.claimed_insurance.claim_id": input_value}))
        if result and isinstance(result[0], dict):
            description = generate_description_by_claim_id(result)
        else:
            description = "No valid records found or data format is incorrect."
    
    return description

@app.route('/download_pdf', methods=['POST'])
def download_pdf():
    description = request.json.get('description', '')
    
    # Generate PDF
    pdf = pdfkit.from_string(description, False, configuration=config)
    
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=patient_data.pdf'
    return response

if __name__ == '__main__':
    app.run(debug=True)
