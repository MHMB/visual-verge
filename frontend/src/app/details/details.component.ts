import {Component, inject} from '@angular/core';
import {CommonModule} from '@angular/common';
import {ActivatedRoute} from '@angular/router';
import {ProductsService} from '../products.service';
import {ProductLocation} from '../product-location';
@Component({
  selector: 'app-details',
  standalone: true,
  imports: [CommonModule],
  template: `
    <article>
      <img
        class="listing-photo"
        [src]="productLocation?.image"
        alt="Exterior photo of {{ productLocation?.name }}"
        crossorigin
      />
      <section class="listing-description">
        <h2 class="listing-heading">{{ productLocation?.name }}</h2>
        <p class="listing-location">{{ productLocation?.id }}, {{ productLocation?.region }}</p>
      </section>
      <section class="listing-features">
        <h2 class="section-heading">About this housing location</h2>
        <ul>
          <li>Off percent: {{ productLocation?.off_percent }}</li>
          <li>Current Price: {{ productLocation?.current_price }}</li>
        </ul>
      </section>
    </article>
  `,
  styleUrls: ['./details.component.css'],
})
export class DetailsComponent {
  route: ActivatedRoute = inject(ActivatedRoute);
  productService = inject(ProductsService);
  productLocation: ProductLocation | undefined;
  constructor() {
    const productLocationId = parseInt(this.route.snapshot.params['id'], 10);
    this.productService.getProductLocationById(productLocationId).then((productLocation) => {
      this.productLocation = productLocation;
    });
  }
}