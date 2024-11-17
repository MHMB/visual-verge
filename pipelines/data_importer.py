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
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from io import BytesIO




def create_robust_session():
    """Create a requests session with retry strategy."""
    session = requests.Session()
    
    # Configure retry strategy
    retries = Retry(
        total=5,  # total number of retries
        backoff_factor=1,  # wait 1, 2, 4, 8, 16 seconds between retries
        status_forcelist=[408, 429, 500, 502, 503, 504],  # HTTP status codes to retry on
        allowed_methods=["GET"],  # only retry on GET requests
    )
    
    # Configure the adapter with the retry strategy
    adapter = HTTPAdapter(
        max_retries=retries,
        pool_connections=100,  # increase connection pool size
        pool_maxsize=100
    )
    
    # Mount the adapter for both HTTP and HTTPS
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session



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

    # Add a new column for human-readable color names
    df['color_names'] = df['colors'].apply(lambda x: convert_rgb_to_names(x if isinstance(x, list) else []))

    # Explode the images column to create a new row for each image
    df['images'] = df['images'].apply(lambda x: x if isinstance(x, list) else [])
    df = df.explode('images').reset_index(drop=True)
    df.dropna(subset=['images'], inplace=True)

    return df



def encode_text(text, processor, model):
    """Encode text using CLIP model."""
    inputs = processor(text=text, return_tensors="pt", padding=True, truncation=True)
    with torch.no_grad():
        output = model.get_text_features(**inputs)
    return output.numpy()


def encode_image(image_url, processor, model, max_retries=3, retry_delay=2):
    """Encode image using CLIP model with robust error handling."""
    session = create_robust_session()
    
    for attempt in range(max_retries):
        try:
            # Set longer timeout and verify SSL
            response = session.get(
                image_url,
                timeout=30,  # increased timeout
                verify=True,  # verify SSL certificates
                stream=True
            )
            response.raise_for_status()
            
            # Read image data into memory
            image_data = BytesIO(response.content)
            image = Image.open(image_data).convert("RGB")
            
            # Process image with CLIP
            inputs = processor(images=image, return_tensors="pt", padding=True)
            with torch.no_grad():
                output = model.get_image_features(**inputs)
            
            return output.numpy()
            
        except requests.exceptions.SSLError as e:
            if attempt < max_retries - 1:
                print(f"SSL error for {image_url}, attempt {attempt + 1}/{max_retries}: {str(e)}")
                time.sleep(retry_delay * (attempt + 1))  # exponential backoff
                continue
            print(f"Final SSL error for {image_url}: {str(e)}")
            return None
            
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                print(f"Request error for {image_url}, attempt {attempt + 1}/{max_retries}: {str(e)}")
                time.sleep(retry_delay * (attempt + 1))
                continue
            print(f"Final request error for {image_url}: {str(e)}")
            return None
            
        except Exception as e:
            print(f"Error processing image {image_url}: {str(e)}")
            return None
        
        finally:
            # Clean up
            if 'response' in locals():
                response.close()
            session.close()


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


def process_products(df: pd.DataFrame, collection_name: str, batch_size: int = 50):
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
    failed_count = 0
    row_count = 0

    for row in df.itertuples(index=False):
        row_count += 1
        try:
            # Encode text
            text = f"{row.name} {row.description}"
            text_vector = encode_text(text, processor, model)

            image_vector = encode_image(row.images, processor, model)
            if image_vector is None:
                continue
            point_id = int(f"{row.id}")

            combined_vector = np.mean([text_vector[0], image_vector[0]], axis=0)

            point = PointStruct( id=point_id, vector=combined_vector.tolist(), payload={ "product_id": row.id, "name": row.name, "description": row.description, "material": row.material, "rating": row.rating, "code": row.code, "brand_id": row.brand_id, "brand_name": row.brand_name, "category_id": row.category_id, "category_name": row.category_name, "gender_id": row.gender_id, "gender_name": row.gender_name, "shop_id": row.shop_id, "shop_name": row.shop_name, "link": row.link, "status": row.status, "colors": row.colors, "sizes": row.sizes, "region": row.region, "currency": row.currency, "current_price": row.current_price, "old_price": row.old_price, "off_percent": row.off_percent, "update_date": row.update_date, "color_names": row.color_names, "image_url": row.images } ) 
            points.append(point)
            if len(points) >= batch_size:
                    try:
                        client.upsert(
                            collection_name=collection_name,
                            points=points
                        )
                        processed_count += len(points)
                        print(f"Inserted {processed_count} points.")
                        print(f"Processed {row_count} rows")
                        points = []
                    except Exception as e:
                        print(f"Error inserting batch: {str(e)}")
                        points = []
        except Exception as e:
            print(f"Error processing product {row['id']}: {str(e)}")
            failed_count += 1
            continue
    
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
    collection_name = "products_3"
    batch_size = 2
    
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