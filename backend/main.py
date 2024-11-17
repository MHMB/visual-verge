from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from transformers import CLIPProcessor, CLIPModel
from qdrant_client import QdrantClient
import torch

app = FastAPI()

# Allow CORS for all origins (for development purposes)
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Query(BaseModel):
    text_query: str = Field(..., description="Text query")

class SearchResult(BaseModel):
    product_id: int
    name: str
    description: str
    image_url: str
    link: str
    score: float

class SemanticSearchService:
    def __init__(
        self,
        collection_name: str = "products",
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        model_name: str = "openai/clip-vit-base-patch32",
    ):
        """Initialize the search service with CLIP model and Qdrant client."""
        # Initialize Qdrant client
        self.collection_name = collection_name
        self.qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)
        
        # Initialize CLIP model and processor
        self.model = CLIPModel.from_pretrained(model_name)
        self.processor = CLIPProcessor.from_pretrained(model_name)
        
        # Move model to GPU if available
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        
    def encode_text(self, text: str) -> List[float]:
        """Encode text query into vector using CLIP."""
        inputs = self.processor(
            text=text,
            return_tensors="pt",
            padding=True,
            truncation=True
        )
        
        # Move inputs to same device as model
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            text_features = self.model.get_text_features(**inputs)
            
        # Return normalized features
        return torch.nn.functional.normalize(text_features, dim=-1)[0].cpu().numpy().tolist()

    def search(
        self,
        text_query: str,
        limit: int = 10,
        score_threshold: float = 0.5
    ) -> List[SearchResult]:
        """
        Search for products using text query.
        
        Args:
            text_query: Text string
            limit: Maximum number of results to return
            score_threshold: Minimum similarity score threshold
            
        Returns:
            List of SearchResult objects sorted by relevance
        """
        query_vector = self.encode_text(text_query)
        
        # Search in Qdrant
        results = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold
        )
        
        # Convert to SearchResult objects
        search_results = []
        for result in results:
            search_results.append(
                SearchResult(
                    product_id=result.payload["product_id"],
                    name=result.payload["name"],
                    description=result.payload["description"],
                    image_url=result.payload["image_url"],
                    link=result.payload["link"],
                    score=result.score
                )
            )
        
        return search_results

# Instantiate the search service
search_service = SemanticSearchService()

@app.post("/search", response_model=List[SearchResult])
def search(query: Query):
    """
    Search for products using text query.
    
    Args:
        query: Text string in JSON format.
    
    Returns:
        List of search results.
    """
    try:
        results = search_service.search(text_query=query.text_query)
        return results
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

