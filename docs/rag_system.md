
**docs/rag_system.md**
```markdown
# RAG System

This document describes the Retrieval-Augmented Generation (RAG) system used in the Public Safety & Urban Planning system.

## Overview

The RAG system combines real-time data with large language models to provide natural language querying capabilities:

1. **Indexing**: Incoming data is embedded and added to a vector index
2. **Retrieval**: Relevant documents are retrieved based on query similarity
3. **Generation**: An LLM generates responses using the retrieved context

## Implementation

The `RAGSystem` class implements this functionality:

```python
class RAGSystem:
    def __init__(self, config: dict):
        self.embedder = embedders.SentenceTransformerEmbedder(model="all-MiniLM-L6-v2")
        self.llm = llms.OpenAIChat(model=config['llm']['model'], ...)
        self.index = KNNIndex()
        self.documents = []
    
    @pw.udf
    def add_document(self, data: pw.Json, source: str, location: pw.Json) -> bool:
        # Add document to knowledge base
    
    def query(self, question: str, k: int = 5) -> str:
        # Query the knowledge base
