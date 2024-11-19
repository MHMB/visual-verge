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

  productLocationList: ProductLocation[] = [];
  productsService: ProductsService = inject(ProductsService);
  filteredProductLocationList: ProductLocation[] = [];
  constructor() {}
  filterResults(text: string) {
    if (!text) {
      this.filteredProductLocationList = this.productLocationList;
      return;
    }
    this.productsService.searchProducts(text).then((productLocationList: ProductLocation[]) => {
      this.productLocationList = productLocationList;
      this.filteredProductLocationList = productLocationList;
    })
    this.filteredProductLocationList = this.productLocationList.filter(
      (productLocation) => productLocation?.name.toLowerCase().includes(text.toLowerCase())
    );
  }
}