from pinecone import Pinecone, ServerlessSpec
from config import Config
import time

class Storage:
    def __init__(self, client):
        """
        Initialize the Storage class with an OpenAI client for handling embeddings and a Pinecone client for database operations.
        
        Args:
            client (OpenAI Client): An instance of the OpenAI client used to generate text embeddings.
        """
        self.client = client
        self.pc = Pinecone(api_key=Config.PINECONE_API_KEY)  # Initialize the Pinecone client with the API key from config.
        self.index_name = Config.PINECONE_INDEX_NAME  # Set the index name from the configuration file.
        self.index = None 

    def manage_index(self):
        """
        Manages the Pinecone index by ensuring only one index exists.
        If an index exists, it is deleted before a new one is created.
        """
        # Retrieve all existing indexes
        existing_indexes = [index["name"] for index in self.pc.list_indexes()]

        # Delete existing index if it exists
        if self.index_name in existing_indexes:
            print(f"Deleting existing index: {self.index_name}")
            self.pc.delete_index(self.index_name)
            # Optional: wait for deletion to confirm
            time.sleep(2)  # Wait to ensure deletion is processed

        # Create a new index
        print(f"Creating new index: {self.index_name}")
        self.pc.create_index(
            self.index_name,
            dimension=Config.PINECONE_DIMENSION,
            metric=Config.PINECONE_METRIC,
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
        # Ensure the index is ready
        while not self.pc.describe_index(self.index_name).status['ready']:
            print("Waiting for index to be ready...")
            time.sleep(1)

        # Connect to the index
        self.index = self.pc.Index(self.index_name)

    def insert_documents(self, extracted_analysed_pages):
        """
            Inserts documents into the Pinecone index with their embeddings and associated metadata.
            
            Args:
                extracted_analysed_pages (list of dict): A list of dictionaries where each dictionary contains page information such as page number and content.
            """
        vectors = []
        for item in extracted_analysed_pages:
            # Create embeddings for each page's content.
            embedding = self.client.embeddings.create(input=item["content"], model=Config.TEXT_EMBEDDING_MODEL).data[0].embedding
            metadata = {'page_number': item["pageNumber"], 'text': item["content"]}
            vectors.append((item["pageNumber"], embedding, metadata))

        # Upsert the vectors into the Pinecone index 
        response = self.index.upsert(vectors)
        print(f"Upsert response: {response}")

        if self.wait_for_index_update(len(extracted_analysed_pages)):
            print(f"The index info just after upserting pages {self.index.describe_index_stats()}")
        else:
            print("Index update timeout reached")


    def wait_for_index_update(self, expected_count, timeout=30):
        """
        Wait for the index to update with the expected number of vectors.   
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            stats = self.index.describe_index_stats()
            if stats['total_vector_count'] >= expected_count:
                return True
            time.sleep(2)  # Wait for 2 seconds before checking again
        return False

