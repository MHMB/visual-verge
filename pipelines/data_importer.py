import os
import json
from itertools import islice
from multiprocessing import Pool, cpu_count

import numpy as np
import torch
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import requests
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams


def load_data():
    # Load product data
    try:
        with open("../data/products_1.json") as file:
            data = json.load(file)
        print("Data loaded successfully!")
    except FileNotFoundError:
        print("File not found. Please check the path.")
    except json.JSONDecodeError:
        print("Error decoding JSON. Please check the file format.")

    # Preprocess data
    processed_data = [
        {
            "id": product["id"],
            "name": product["name"],
            "description": product["description"] or "",
            "images": product["images"],
            "link": product["link"],
        }
        for product in data
        if product.get("images")
    ]

    return processed_data


def chunk_data(data, chunk_size):
    """Yield successive chunks from the dataset."""
    it = iter(data)
    while chunk := list(islice(it, chunk_size)):
        yield chunk


def encode_text(text, processor, model):
    inputs = processor(text=text, return_tensors="pt", padding=True, truncation=True)
    return model.get_text_features(**inputs).detach().numpy()


def encode_image(image_url, processor, model):
    response = requests.get(image_url, stream=True)
    image = Image.open(response.raw).convert("RGB")
    inputs = processor(images=image, return_tensors="pt", padding=True)
    return model.get_image_features(**inputs).detach().numpy()


def create_collection(collection_name):
    # Connect to Qdrant
    qdrant = QdrantClient("http://localhost:6333")

    if not qdrant.collection_exists(collection_name):
        qdrant.create_collection(
            collection_name=collection_name,
            vectors_config={
                "image_vector": VectorParams(size=512, distance="Cosine"),
                "text_vector": VectorParams(size=512, distance="Cosine"),
            },
        )
        print(f"Collection '{collection_name}' created.")
    else:
        print(f"Collection '{collection_name}' already exists.")
    return qdrant


def process_chunk(chunk, collection_name, qdrant_url, processor, model):
    """Process a single chunk and insert points into Qdrant."""
    for product in chunk:
        text_embedding = encode_text(f"{product['name']} {product['description']}", processor, model)
        for image_url in product["images"]:
            # Encode image
            image_embedding = encode_image(image_url, processor, model)
            
            # Prepare data for insertion
            point = {
                "id": int(product["id"]),  # Ensure the ID is an integer
                "vectors": {
                    "image_vector": image_embedding.tolist(),
                    "text_vector": text_embedding.tolist()
                },
                "payload": {
                    "name": product["name"],
                    "link": product["link"],
                    "description": product["description"]
                }
            }
            
            # Insert point using raw HTTP request
            response = requests.put(
                f"{qdrant_url}/collections/{collection_name}/points",
                json={"points": [point]}
            )
            if response.status_code == 200:
                print(f"Inserted point for product ID {product['id']}.")
            else:
                print(f"Failed to insert point for product ID {product['id']}: {response.text}")


def main():
    collection_name = "products"
    qdrant_url = "http://localhost:6333"
    
    # Load data and initialize model and processor
    processed_data = load_data()
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    model.config.text_config.max_position_embeddings = 2048
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

    # Create the collection
    create_collection(collection_name)

    # Define chunk size
    chunk_size = 100  # Adjust based on dataset size and available memory

    # Create a list of chunks
    data_chunks = list(chunk_data(processed_data, chunk_size))

    # Set up multiprocessing pool
    num_workers = min(cpu_count(), len(data_chunks))  # Use all available CPUs
    with Pool(num_workers) as pool:
        pool.starmap(
            process_chunk,
            [(chunk, collection_name, qdrant_url, processor, model) for chunk in data_chunks],
        )


if __name__ == "__main__":
    main()
