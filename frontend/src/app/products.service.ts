import { Injectable } from '@angular/core';
import { ProductLocation } from './product-location';

@Injectable({
  providedIn: 'root'
})
export class ProductsService {
  url = 'http://localhost:8000/search';

  
  async getAllProductLocations(): Promise<ProductLocation[]> {
    const data = await fetch(this.url);
    return (await data.json()) ?? [];
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
