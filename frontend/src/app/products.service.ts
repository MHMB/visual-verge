import { Injectable } from '@angular/core';
import { ProductLocation } from './product-location';

@Injectable({
  providedIn: 'root'
})
export class ProductsService {
  url = 'http://localhost:8000/search';

  
  async searchProducts(text_query: string, filters: any = {}, limit: number = 10): Promise<ProductLocation[]> {
    const postBody = {
        text_query,
        filters,
        limit
    };

    const response = await fetch(this.url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(postBody)
    });

    return (await response.json()) ?? [];
}


  async getProductLocationById(id: number): Promise<ProductLocation | undefined> {
    const data = await fetch(`${this.url}/${id}`);
    return (await data.json()) ?? {};
  }
  submitApplication(firstName: string, lastName: string, email: string) {
    // tslint:disable-next-line
    console.log(firstName, lastName, email);
  }
}
