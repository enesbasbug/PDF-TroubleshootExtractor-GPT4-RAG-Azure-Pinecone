import json
from config import Config  # Import configuration settings such as API keys and model names

class Search:
    def __init__(self, client):
        """
        Initialize the Search class with an OpenAI client.
        Args:
            client (OpenAI Client): An instance of the OpenAI client to interact with OpenAI's API.
        """
        self.client = client

    def rag_search(self, index, query, top_k=5):
        """
        Perform a Retrieval-Augmented Generation (RAG) search using Pinecone's vector search to find the most relevant pages.
        
        Args:
            index (Pinecone Index): The Pinecone index where document vectors are stored.
            query (str): The query string to search for.
            top_k (int): The number of top results to return.
        
        Returns:
            dict: The search results including metadata.
        """
        # Generate an embedding for the query using the configured text embedding model
        query_embedding = self.client.embeddings.create(input=query, model=Config.TEXT_EMBEDDING_MODEL).data[0].embedding
        # Perform the query using the generated embedding
        results = index.query(vector=query_embedding, top_k=top_k, include_metadata=True)
        print("RAG Search Results:", results)
        return results

    def gpt4(self, related_source):
        """
        Utilises GPT-4 to analyze the search results and extract the page number with its content about the Troubleshooting section.
        
        Args:
            related_source (str): The related pages related to troubleshooting received from Pinecone DB.
        
        Returns:
            str: JSON formatted string with the page number and related text or a failure message.
        """

        system_prompt = (
            "You are an intelligent assistant that finds a page about Troubleshooting."
            + " You will be given some documents, return the number of the page that is about the Troubleshooting Section."
            + " If you find that page, include page source as citation with page number and return them in JSON format:"
            + "\n{'pageNumber': pageNumber, 'pageSource': text_from_documents_related_to_troubleshooting}"
            + "\n\n If you cannot find any related page, return:"
            + "\n{'output': 'could not find Troubleshooting page'}"
        )
        user_prompt = (
            "Here are the documents below. Return the page number"
            + f" and the text related to Troubleshooting as a JSON data \n\n {related_source}"
        )
        
        response = self.client.chat.completions.create(
            model=Config.GPT_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
                ],
            temperature=0.4)
        result = response.choices[0].message.content.strip()
        # print("GPT-4 Response:", result)
        return result

    def find_page_related_to_troubleshooting(self, index):
        query = "what is the page number of troubleshooting section that mentions Troubleshooting Condition/Problem Console"
        related_source = self.rag_search(index, query)
        page_info = self.gpt4(related_source)
        page_info_json = json.loads(page_info)  # Convert the JSON string from GPT-4 into a dictionary
        return page_info_json
