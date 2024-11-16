import os
import json

import numpy as np
import torch
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import requests
from qdrant_client import QdrantClient
from qdrant_client.http.models import CollectionInfo, VectorParams, PointStruct

# Load product data
try:
    with open('../data/products_1.json') as file:
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
        "link": product["link"]
    }
    for product in data if product.get('images')
]

# Initialize CLIP model and processor
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

def encode_text(text):
    inputs = processor(text=text, return_tensors="pt", padding=True)
    return model.get_text_features(**inputs).detach().numpy()

def encode_image(image_url):
    response = requests.get(image_url, stream=True)
    image = Image.open(response.raw).convert("RGB")
    inputs = processor(images=image, return_tensors="pt", padding=True)
    return model.get_image_features(**inputs).detach().numpy()

# Connect to Qdrant
qdrant = QdrantClient("http://localhost:6333")

# Ensure collection exists or create it
collection_name = "products"
if not qdrant.collection_exists(collection_name):
    qdrant.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=512, distance="Cosine")
    )
    print(f"Collection '{collection_name}' created.")
else:
    print(f"Collection '{collection_name}' already exists.")

# Insert data
for product in processed_data:
    text_embedding = encode_text(f"{product['name']} {product['description']}")
    for image_url in product['images']:
        image_embedding = encode_image(image_url)
        point = PointStruct(
            id=str(product['id']),  # Ensure ID is a string
            vector=image_embedding.tolist(),
            payload={
                "name": product["name"],
                "link": product["link"],
                "text_embedding": text_embedding.tolist()
            }
        )
        qdrant.upsert(collection_name=collection_name, points=[point])
        print(f"Inserted point for product ID {product['id']}.")
