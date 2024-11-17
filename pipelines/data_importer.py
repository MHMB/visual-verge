import json
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import requests
import torch
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

import pandas as pd
import json
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.impute import SimpleImputer
from datetime import datetime
from webcolors import hex_to_name

def convert_rgb_to_names(colors):
        color_names = []
        for color in colors:
            try:
                # Convert RGB to the closest color name
                color_names.append(hex_to_name(color))
            except ValueError:
                color_names.append("Unknown")  # Handle unmapped colors
        return color_names


def load_data(file_path):
    # Load JSON data
    with open(file_path, 'r') as file:
        data = json.load(file)

    # Convert to DataFrame
    df = pd.DataFrame(data)

    # Convert RGB colors to human-readable names
    def convert_rgb_to_names(colors):
        color_names = []
        for color in colors:
            try:
                # Convert RGB to the closest color name
                color_names.append(hex_to_name(color))
            except ValueError:
                color_names.append("Unknown")  # Handle unmapped colors
        return color_names

    # Add a new column for human-readable color names
    df['color_names'] = df['colors'].apply(lambda x: convert_rgb_to_names(x if isinstance(x, list) else []))

    # Explode the images column to create a new row for each image
    df['images'] = df['images'].apply(lambda x: x if isinstance(x, list) else [])
    df = df.explode('images').reset_index(drop=True)

    return df



def encode_text(text, processor, model):
    """Encode text using CLIP model."""
    inputs = processor(text=text, return_tensors="pt", padding=True, truncation=True)
    with torch.no_grad():
        output = model.get_text_features(**inputs)
    return output.numpy()


def encode_image(image_url, processor, model):
    """Encode image using CLIP model."""
    try:
        response = requests.get(image_url, stream=True)
        image = Image.open(response.raw).convert("RGB")
        inputs = processor(images=image, return_tensors="pt", padding=True)
        with torch.no_grad():
            output = model.get_image_features(**inputs)
        return output.numpy()
    except Exception as e:
        print(f"Error processing image {image_url}: {str(e)}")
        return None


def create_collection(client: QdrantClient, collection_name: str):
    """Create or recreate Qdrant collection."""
    # Delete existing collection if it exists
    if client.collection_exists(collection_name):
        client.delete_collection(collection_name)
        print(f"Existing collection '{collection_name}' deleted.")

    # Create new collection
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=512,  # CLIP embedding size
            distance=Distance.COSINE
        )
    )
    print(f"Collection '{collection_name}' created.")


def process_products(products, collection_name: str, batch_size: int = 50):
    """Process products and insert into Qdrant."""
    # Initialize Qdrant client
    client = QdrantClient("localhost", port=6333)
    
    # Initialize CLIP model and processor
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    
    # Create collection
    create_collection(client, collection_name)
    
    # Process products in batches
    points = []
    processed_count = 0
    
    for product in products:
        # Encode text
        text = f"{product['name']} {product['description']}"
        text_vector = encode_text(text, processor, model)
        
        # Process each image for the product
        for idx, image_url in enumerate(product["images"]):
            image_vector = encode_image(image_url, processor, model)
            if image_vector is None:
                continue
            
            # Create unique ID for each image-text pair
            point_id = int(f"{product['id']}{idx:03d}")
            
            # Average text and image vectors
            combined_vector = np.mean([text_vector[0], image_vector[0]], axis=0)
            
            # Create point
            point = PointStruct(
                id=point_id,
                vector=combined_vector.tolist(),
                payload={
                    "product_id": product["id"],
                    "name": product["name"],
                    "description": product["description"],
                    "link": product["link"],
                    "image_url": image_url
                }
            )
            points.append(point)
            
            # Insert batch when reaching batch_size
            if len(points) >= batch_size:
                try:
                    client.upsert(
                        collection_name=collection_name,
                        points=points
                    )
                    processed_count += len(points)
                    print(f"Inserted {processed_count} points.")
                    points = []
                except Exception as e:
                    print(f"Error inserting batch: {str(e)}")
                    points = []
    
    # Insert remaining points
    if points:
        try:
            client.upsert(
                collection_name=collection_name,
                points=points
            )
            processed_count += len(points)
            print(f"Inserted final batch. Total points inserted: {processed_count}")
        except Exception as e:
            print(f"Error inserting final batch: {str(e)}")


def search_products(query_text: str, collection_name: str, limit: int = 5):
    """Search products using text query."""
    client = QdrantClient("localhost", port=6333)
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    
    # Encode query text
    query_vector = encode_text(query_text, processor, model)[0]
    
    # Search in Qdrant
    results = client.search(
        collection_name=collection_name,
        query_vector=query_vector.tolist(),
        limit=limit
    )
    
    return results


def main():
    collection_name = "products"
    batch_size = 100
    
    # Load data
    print("Loading data...")
    products = load_data("../data/products_1.json")
    print(f"Loaded {len(products)} products.")
    
    # Process products and insert into Qdrant
    print("Processing products...")
    process_products(products, collection_name, batch_size)
    
    # # Test search
    # print("\nTesting search functionality...")
    # query = "blue dress"
    # results = search_products(query, collection_name)
    # print(f"\nSearch results for '{query}':")
    # for idx, result in enumerate(results, 1):
    #     print(f"{idx}. {result.payload['name']} (Score: {result.score:.3f})")


if __name__ == "__main__":
    main()