import { Component } from '@angular/core';
import {CommonModule} from '@angular/common';
import {ProductLocationComponent} from "../product-location/product-location.component";
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
      <app-product-location></app-product-location>
    </section>
  `,
  styleUrls: ['./nav-bar.component.css']
})
export class NavBarComponent {

}
