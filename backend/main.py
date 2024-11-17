from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from transformers import CLIPProcessor, CLIPModel
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, Range, MatchValue, MatchAny
import torch

app = FastAPI()

# Allow CORS
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PriceFilter(BaseModel):
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    currency: Optional[str] = None

class FilterParams(BaseModel):
    price: Optional[PriceFilter] = None
    region: Optional[List[str]] = None
    sizes: Optional[List[str]] = None
    color_names: Optional[List[str]] = None
    gender_name: Optional[List[str]] = None
    category_name: Optional[List[str]] = None
    brand_name: Optional[List[str]] = None

class Query(BaseModel):
    text_query: str = Field(..., description="Text query for semantic search")
    filters: Optional[FilterParams] = Field(default=None, description="Optional filters")
    limit: Optional[int] = Field(default=10, description="Maximum number of results to return", ge=1, le=100)

class SearchResult(BaseModel):
    product_id: int
    name: str
    description: str
    image_url: str
    link: str
    score: float
    current_price: float
    currency: str
    color_names: List[str]
    sizes: List[str]
    region: str
    brand_name: str
    category_name: str
    gender_name: str

class SemanticSearchService:
    def __init__(
        self,
        collection_name: str = "products",
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        model_name: str = "openai/clip-vit-base-patch32",
    ):
        self.collection_name = collection_name
        self.qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)
        self.model = CLIPModel.from_pretrained(model_name)
        self.processor = CLIPProcessor.from_pretrained(model_name)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
    
    def build_filter(self, filters: Optional[FilterParams]) -> Optional[Filter]:
        """Build Qdrant filter from filter parameters."""
        if not filters:
            return None

        must_conditions = []

        # Price filter
        if filters.price:
            if filters.price.min_price is not None:
                must_conditions.append(
                    FieldCondition(
                        key="current_price",
                        range=Range(gte=filters.price.min_price)
                    )
                )
            if filters.price.max_price is not None:
                must_conditions.append(
                    FieldCondition(
                        key="current_price",
                        range=Range(lte=filters.price.max_price)
                    )
                )
            if filters.price.currency:
                must_conditions.append(
                    FieldCondition(
                        key="currency",
                        match=MatchValue(value=filters.price.currency)
                    )
                )

        # Array field filters
        if filters.region:
            must_conditions.append(
                FieldCondition(key="region", match=MatchAny(any=filters.region))
            )
        if filters.sizes:
            must_conditions.append(
                FieldCondition(key="sizes", match=MatchAny(any=filters.sizes))
            )
        if filters.color_names:
            must_conditions.append(
                FieldCondition(key="color_names", match=MatchAny(any=filters.color_names))
            )
        if filters.gender_name:
            must_conditions.append(
                FieldCondition(key="gender_name", match=MatchAny(any=filters.gender_name))
            )
        if filters.category_name:
            must_conditions.append(
                FieldCondition(key="category_name", match=MatchAny(any=filters.category_name))
            )
        if filters.brand_name:
            must_conditions.append(
                FieldCondition(key="brand_name", match=MatchAny(any=filters.brand_name))
            )

        return Filter(must=must_conditions) if must_conditions else None

    def encode_text(self, text: str) -> List[float]:
        """Encode text query into vector using CLIP."""
        inputs = self.processor(
            text=text,
            return_tensors="pt",
            padding=True,
            truncation=True
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            text_features = self.model.get_text_features(**inputs)
        return torch.nn.functional.normalize(text_features, dim=-1)[0].cpu().numpy().tolist()

    def search(
        self,
        text_query: str,
        filters: Optional[FilterParams] = None,
        limit: int = 10,
        score_threshold: float = 0.5
    ) -> List[SearchResult]:
        """Search for products using text query and optional filters."""
        query_vector = self.encode_text(text_query)
        qdrant_filter = self.build_filter(filters)
        
        results = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=qdrant_filter
        )
        
        return [
            SearchResult(
                product_id=result.payload["product_id"],
                name=result.payload["name"],
                description=result.payload["description"],
                image_url=result.payload["image_url"],
                link=result.payload["link"],
                score=result.score,
                current_price=result.payload["current_price"],
                currency=result.payload["currency"],
                color_names=result.payload["color_names"],
                sizes=result.payload["sizes"],
                region=result.payload["region"],
                brand_name=result.payload["brand_name"],
                category_name=result.payload["category_name"],
                gender_name=result.payload["gender_name"]
            )
            for result in results
        ]

# Instantiate the search service
search_service = SemanticSearchService()

@app.post("/search", response_model=List[SearchResult])
async def search(query: Query):
    """
    Search for products using text query and optional filters.
    
    Only text_query is required, all filters are optional.
    
    Minimal example:
    {
        "text_query": "blue dress"
    }
    
    Full example with all optional filters:
    {
        "text_query": "blue dress",
        "filters": {
            "price": {
                "min_price": 50,
                "max_price": 200,
                "currency": "USD"
            },
            "region": ["US"],
            "sizes": ["M", "L"],
            "color_names": ["blue", "navy"],
            "gender_name": ["Women"],
            "category_name": ["Dresses"],
            "brand_name": ["Zara"]
        },
        "limit": 10
    }
    """
    try:
        results = search_service.search(
            text_query=query.text_query,
            filters=query.filters,
            limit=query.limit
        )
        return results
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))