import pathway as pw
from pathway.xpacks.llm import embedders, llms
from pathway.stdlib.ml.index import KNNIndex
import json

class RAGSystem:
    def __init__(self, config: dict):
        self.config = config
        self.embedder = embedders.SentenceTransformerEmbedder(
            model="all-MiniLM-L6-v2"
        )
        self.llm = llms.OpenAIChat(
            model=config['llm']['model'],
            api_key=config['llm']['api_key'],
            temperature=config['llm'].get('temperature', 0.3)
        )
        self.index = KNNIndex()
        self.documents = []
    
    @pw.udf
    def add_document(self, data: pw.Json, source: str, location: pw.Json) -> bool:
        doc = {
            "timestamp": pw.now().strftime('%Y-%m-%dT%H:%M:%S.%f'),
            "source": source,
            "data": data,
            "location": location
        }
        
        # Create text representation for embedding
        text = f"{source}: {json.dumps(data)} at {location['lat']},{location['lon']}"
        
        # Embed and add to index
        embedding = self.embedder.embed_query(text)
        self.index.add_document(embedding, doc)
        self.documents.append(doc)
        
        return True
    
    def query(self, question: str, k: int = 5) -> str:
        # Embed the question
        question_embedding = self.embedder.embed_query(question)
        
        # Retrieve relevant documents
        results = self.index.query(question_embedding, k=k)
        
        # Prepare context for LLM
        context = "\n\n".join([
            f"Source: {doc['source']}\nData: {json.dumps(doc['data'])}\nLocation: {doc['location']}"
            for doc in results
        ])
        
        # Generate answer with LLM
        prompt = f"""Based on the following real-time data, answer the question.
        
Context:
{context}

Question: {question}

Answer:"""
        
        return self.llm.generate(prompt)
