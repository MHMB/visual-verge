import { Injectable } from '@angular/core';
import { ProductLocation } from './product-location';

@Injectable({
  providedIn: 'root'
})
export class ProductsService {
  readonly baseUrl = 'https://angular.dev/assets/images/tutorials/common';
  protected productLocationList: ProductLocation[] = [
    {
      id: "9999",
      name: 'Test Home',
      image: "https://media.6media.me/media/catalog/product/cache/51d09e6ba6f1fb68e23a90a2eb71ff17/a/t/atlanticus_black_001-002-043_alt3_sq_nt_4800x4800.jpg",
      region: "SAUDI",
      shop_name: "6thstreet",
      current_price: 100,
      off_percent: 3,
    },
    {
      id: "2089163",
      name: 'Lydia Millen Cutwork and Embroidery Bandeau Dress',
      image: "https://media.6media.me/media/catalog/product/cache/51d09e6ba6f1fb68e23a90a2eb71ff17/a/t/atlanticus_black_001-002-043_alt3_sq_nt_4800x4800.jpg",
      region: "QATAR",
      shop_name: "6thstreet",
      current_price: 100,
      off_percent: 3,
    },
    {
      id: "2089164",
      name: 'Twill Column Bridesmaids Dress',
      image: "https://media.6media.me/media/catalog/product/cache/51d09e6ba6f1fb68e23a90a2eb71ff17/b/c/bcc06950_black_xl.jpg",
      region: "QATAR",
      shop_name: "6thstreet",
      current_price: 100,
      off_percent: 3,
    },
    {
      id: "2089163",
      name: 'Test Home',
      image: "https://media.6media.me/media/catalog/product/cache/51d09e6ba6f1fb68e23a90a2eb71ff17/a/t/atlanticus_black_001-002-043_alt3_sq_nt_4800x4800.jpg",
      region: "OMAN",
      shop_name: "6thstreet",
      current_price: 100,
      off_percent: 3,
    }
  ];
  getAllProductLocations(): ProductLocation[]{
    return this.productLocationList
  }

  getHousingLocationById(id: string): ProductLocation | undefined{
    return this.productLocationList.find((productLocation) => productLocation.id === id);
  }
}
