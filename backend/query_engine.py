from typing import List, Optional, Union
from dataclasses import dataclass
import torch
from transformers import CLIPProcessor, CLIPModel
from qdrant_client import QdrantClient
from PIL import Image
import requests
import matplotlib.pyplot as plt 
import matplotlib.image as mpimg 
from urllib.request import urlopen 
import numpy as np
import io


@dataclass
class SearchResult:
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

    def encode_image(self, image: Union[str, Image.Image]) -> List[float]:
        """Encode image query into vector using CLIP."""
        # Handle image input as URL or PIL Image
        if isinstance(image, str):
            response = requests.get(image, stream=True)
            image = Image.open(response.raw).convert("RGB")
        
        inputs = self.processor(
            images=image,
            return_tensors="pt",
            padding=True
        )
        
        # Move inputs to same device as model
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            image_features = self.model.get_image_features(**inputs)
            
        # Return normalized features
        return torch.nn.functional.normalize(image_features, dim=-1)[0].cpu().numpy().tolist()

    def search(
        self,
        query: Union[str, Image.Image],
        limit: int = 10,
        score_threshold: Optional[float] = 0.5
    ) -> List[SearchResult]:
        """
        Search for products using text or image query.
        
        Args:
            query: Text string or PIL Image
            limit: Maximum number of results to return
            score_threshold: Minimum similarity score threshold
            
        Returns:
            List of SearchResult objects sorted by relevance
        """
        # Encode query based on type
        if isinstance(query, str):
            query_vector = self.encode_text(query)
        else:
            query_vector = self.encode_image(query)
        
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

    def search_with_filters(
        self,
        query: Union[str, Image.Image],
        limit: int = 10,
        score_threshold: Optional[float] = 0.5,
        **filters
    ) -> List[SearchResult]:
        """
        Search with additional filters.
        
        Example filters:
        - price_range: tuple[float, float]
        - brands: List[str]
        - categories: List[str]
        """
        # Implement filter logic based on your needs
        # This is a placeholder for future implementation
        return self.search(query, limit, score_threshold)


def visualize_results(results: List[SearchResult]):
    """
    Visualize search results in a grid.
    
    Parameters:
    - results: List of SearchResult objects.
    """
    num_images = len(results)
    grid_size = int(np.ceil(np.sqrt(num_images)))  # Calculate grid size
    
    fig, axes = plt.subplots(grid_size, grid_size, figsize=(15, 15))
    axes = axes.flatten()
    
    for idx, result in enumerate(results):
        response = urlopen(result.image_url)
        img = Image.open(io.BytesIO(response.read())).convert("RGB")
        
        axes[idx].imshow(img)
        axes[idx].axis('off')  # Hide axis
        axes[idx].set_title(result.name, fontsize=12)
    
    # Hide any remaining empty subplots
    for j in range(idx + 1, grid_size * grid_size):
        axes[j].axis('off')
    
    plt.tight_layout()
    plt.show()


def main():
    # Initialize search service
    search_service = SemanticSearchService()
    
    # Example text search
    query_str = input("What are you searching for? ")
    results = search_service.search(query_str, limit=5)
    for result in results:
        print(f"\nProduct: {result.name}")
        print(f"Score: {result.score:.3f}")
        print(f"Link: {result.link}")
    
    visualize_results(results)
    # # Example image search
    # print("\nSearching with image URL:")
    # image_url = "https://example.com/dress.jpg"  # Replace with actual image URL
    # try:
    #     results = search_service.search(image_url, limit=5)
    #     for result in results:
    #         print(f"\nProduct: {result.name}")
    #         print(f"Score: {result.score:.3f}")
    #         print(f"Link: {result.link}")
    # except Exception as e:
    #     print(f"Error searching with image: {str(e)}")


if __name__ == "__main__":
    main()