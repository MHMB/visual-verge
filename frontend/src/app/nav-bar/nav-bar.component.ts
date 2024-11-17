import { Component } from '@angular/core';
import {CommonModule} from '@angular/common';
import {ProductLocationComponent} from "../product-location/product-location.component";
import {ProductLocation} from "../product-location";
@Component({
  selector: 'app-nav-bar',
  standalone: true,
  imports: [CommonModule, ProductLocationComponent],
  template: `
    <section>
      <form>
        <input type="text" placeholder="Search for product!" />
        <button class="primary" type="button">Search</button>
      </form>
    </section>
    <section class="results">
      <app-product-location
          *ngFor="let productLocation of productLocationList"
          [productLocation]="productLocation"
        ></app-product-location>
    </section>
  `,
  styleUrls: ['./nav-bar.component.css']
})
export class NavBarComponent {
  readonly baseUrl = 'https://angular.dev/assets/images/tutorials/common';
  productLocationList: ProductLocation[] = [
    {
      id: "9999",
      name: 'Test Home',
      image: "https://media.6media.me/media/catalog/product/cache/51d09e6ba6f1fb68e23a90a2eb71ff17/a/t/atlanticus_black_001-002-043_alt3_sq_nt_4800x4800.jpg",
      region: "SAUDI"
    },
    {
      id: "2089163",
      name: 'Lydia Millen Cutwork and Embroidery Bandeau Dress',
      image: "https://media.6media.me/media/catalog/product/cache/51d09e6ba6f1fb68e23a90a2eb71ff17/a/t/atlanticus_black_001-002-043_alt3_sq_nt_4800x4800.jpg",
      region: "QATAR"
    },
    {
      id: "2089164",
      name: 'Twill Column Bridesmaids Dress',
      image: "https://media.6media.me/media/catalog/product/cache/51d09e6ba6f1fb68e23a90a2eb71ff17/b/c/bcc06950_black_xl.jpg",
      region: "QATAR"
    },
    {
      id: "2089163",
      name: 'Test Home',
      image: "https://media.6media.me/media/catalog/product/cache/51d09e6ba6f1fb68e23a90a2eb71ff17/a/t/atlanticus_black_001-002-043_alt3_sq_nt_4800x4800.jpg",
      region: "OMAN"
    }
  ];
}