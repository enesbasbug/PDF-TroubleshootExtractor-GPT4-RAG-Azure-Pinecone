import configparser
import os
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient

class DataExtract:
    def __init__(self):
        """
        Initialize the DataExtract class by setting up the Azure Document Analysis client using API credentials.
        """
        self.client = self.initialize_client()

    def initialize_client(self):
        """
        Read the Azure API credentials from a configuration file and create a DocumentAnalysisClient.

        Returns:
            DocumentAnalysisClient: A client object used for connecting to Azure's Document Analysis service.
        """
        config = configparser.ConfigParser()
        config.read('azure.ini')  # Read the configuration file that stores the Azure API key and endpoint.
        api_key = config.get('ai-azure-test', 'azure_api_key')  # Retrieve the API key from the configuration.
        endpoint = config.get('ai-azure-test', 'azure_endpoint')  # Retrieve the endpoint URL from the configuration.
        return DocumentAnalysisClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(api_key)  # Create the client with the endpoint and the API key.
        )

    def extract_data(self, file_stream):
        """
        Extract text data from a file stream using Azure's prebuilt document analysis model.

        Args:
            file_stream (file-like object): The stream of the file to be processed.

        Returns:
            list: A list of dictionaries, each containing the page number and extracted text content.
        """
        model_id = "prebuilt-read"  # Specify the model ID used for document analysis.
        file_data = file_stream.read()  # Read the entire content of the file from the stream.
        poller = self.client.begin_analyze_document(model_id=model_id, document=file_data, locale="en-US")
        result = poller.result()  # Wait for the analysis to complete and retrieve the result.
        return self.analyse_extracted_text(result)

    def analyse_extracted_text(self, result):
        """
        Analyze the text extraction result and organize the data by page.

        Args:
            result (AnalyzeDocumentResult): The result object returned by Azure's Document Analysis service.

        Returns:
            list: A list of dictionaries, where each dictionary contains a page number and its corresponding text content.
        """
        analysed_pages = []
        for page in result.pages:  # Iterate over each page in the document.
            parsed_page = {"pageNumber": f'<Page {page.page_number:03d}>', "content": ""}
            for word in page.words:  # Concatenate all words to form the full text content of the page.
                parsed_page["content"] += word.content + " "
            analysed_pages.append(parsed_page)  # Add the parsed page data to the list.
        return analysed_pages
