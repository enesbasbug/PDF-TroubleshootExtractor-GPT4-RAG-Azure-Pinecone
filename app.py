from flask import Flask, jsonify, request
from azure_data_extract import DataExtract  # Module to handle data extraction from documents using Azure services
from gpt_rag import Search                 # Module to handle search and natural language processing with GPT
from pinecone_database import Storage      # Module to handle database operations with Pinecone
from config import Config                  # Module to handle application configurations and secrets securely
from openai import OpenAI                  # OpenAI library for accessing GPT models


# Initialize the Flask app
app = Flask(__name__)

# Load configuration from config.py
app.config.from_object(Config)


# Define the OpenAI API key and initialize the client for interacting with OpenAI services
openai_api_key = app.config['OPEN_API_KEY']
client = OpenAI(api_key=openai_api_key)

# Initialize classes with dependencies
data_extract = DataExtract()  # Creates an instance of DataExtract for processing documents
storage = Storage(client)     # Creates an instance of Storage, passing the OpenAI client for embedding operations
search = Search(client)       # Creates an instance of Search, also passing the OpenAI client for search operations

@app.route('/api/documents/ingest', methods=['POST'])
def upload_file():
    """
    Endpoint to handle file uploads and process them to find troubleshooting information in PDFs.
    This route listens for POST requests and expects a PDF file as part of the request.
    It processes the file to extract information with Azure, saves it in a Pinecone database, and performs a search to find specific content.
    """
    # Check if the 'file' key is in the uploaded files dictionary
    if 'file' not in request.files:
        return jsonify(error="No file part"), 400  # Return error if no file part in request

    # Get the file from the request
    file = request.files['file']
    
    # Check if the file name is empty (no file uploaded)
    if file.filename == '':
        return jsonify(error="No selected file"), 400

    # Ensure the file is a PDF before processing
    if file and file.filename.endswith('.pdf'):
        index = storage.manage_index() # Reset or initially set up the Pinecone index - for each new PDF file
        try:
            # Extract data from the uploaded PDF
            extracted_analysed_pages = data_extract.extract_data(file)
            print(f"Data extracted successfully! The length of PDF file is: {len(extracted_analysed_pages)} pages.")

            # Initialize and populate the Pinecone database with the extracted data
            storage.insert_documents(extracted_analysed_pages)

            # Find the specific page related to troubleshooting using the Search class
            page_related = search.find_page_related_to_troubleshooting(storage.index)
            return jsonify(page_related)
        
        except Exception as e:
            # Handle exceptions and return an error response
            return jsonify(error=str(e)), 500
    
    # Return an error if the file is not supported (not a PDF)
    return jsonify(error="Unsupported file type"), 400

# Run the Flask application if the script is executed directly
if __name__ == '__main__':
    app.run(debug=True)
