import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ProductLocation } from '../product-location';
import {RouterModule} from '@angular/router';


@Component({
  selector: 'app-product-location',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <section class="listing">
      <img
        class="listing-photo"
        [src]="productLocation.image"
        alt="Exterior photo of {{ productLocation.name }}"
        crossorigin
      />
      <h2 class="listing-heading">{{ productLocation.name }}</h2>
      <p class="listing-location">{{ productLocation.id }}, {{ productLocation.region }}</p>
      <a [routerLink]="['/details', productLocation.id]">details ...</a>
    </section>
  `,
  styleUrls: ['./product-location.component.css'],
})
export class ProductLocationComponent {
  @Input() productLocation!: ProductLocation;
}
