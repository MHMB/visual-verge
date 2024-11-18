import { Component, inject } from '@angular/core';
import {CommonModule} from '@angular/common';
import {ProductLocationComponent} from "../product-location/product-location.component";
import {ProductLocation} from "../product-location";
import { ProductsService } from '../products.service';
@Component({
  selector: 'app-nav-bar',
  standalone: true,
  imports: [CommonModule, ProductLocationComponent],
  template: `
    <section>
      <form>
        <input type="text" placeholder="Search for product!" #filter/>
        <button class="primary" type="button" (click)="filterResults(filter.value)">Search</button>
      </form>
    </section>
    <section class="results">
      <app-product-location
          *ngFor="let productLocation of filteredProductLocationList"
          [productLocation]="productLocation"
        ></app-product-location>
    </section>
  `,
  styleUrls: ['./nav-bar.component.css']
})
export class NavBarComponent {
  readonly baseUrl = 'https://angular.dev/assets/images/tutorials/common';
  productLocationList: ProductLocation[] = [];
  productsService: ProductsService = inject(ProductsService);
  filteredProductLocationList: ProductLocation[] = [];
  constructor() {
    this.productLocationList = this.productsService.getAllProductLocations();
    this.filteredProductLocationList = this.productLocationList
  }
  filterResults(text: string) {
    if (!text) {
      this.filteredProductLocationList = this.productLocationList;
      return;
    }
    this.filteredProductLocationList = this.productLocationList.filter(
      (productLocation) => productLocation?.name.toLowerCase().includes(text.toLowerCase())
    );
  }
}