// src/app/components/search/search.component.ts

import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';

// Material Imports
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatSelectModule } from '@angular/material/select';
import { MatFormFieldModule } from '@angular/material/form-field';
import { provideNativeDateAdapter } from '@angular/material/core';

import { SearchService } from '../../services/search.service';
import { SearchRequest } from '../../types/search.types';

@Component({
  selector: 'app-search',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    HttpClientModule,
    // Material Modules
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatExpansionModule,
    MatSelectModule,
    MatFormFieldModule,
  ],
  providers: [provideNativeDateAdapter()],
  templateUrl: './search.component.html',
  styleUrl: './search.component.css'
})
export class SearchComponent implements OnInit {
  searchForm: FormGroup;
  isFiltersPanelExpanded = false;

  // Sample data - replace with actual data from your API
  availableRegions = ['North America', 'Europe', 'Asia'];
  availableSizes = ['XS', 'S', 'M', 'L', 'XL'];
  availableColors = ['Black', 'White', 'Red', 'Blue'];
  availableGenders = ['Men', 'Women', 'Unisex'];
  availableCategories = ['Shirts', 'Pants', 'Shoes'];
  availableBrands = ['Nike', 'Adidas', 'Puma'];

  constructor(
    private fb: FormBuilder,
    private searchService: SearchService
  ) {
    this.searchForm = this.fb.group({
      text_query: [''],
      filters: this.fb.group({
        price: this.fb.group({
          min_price: [0],
          max_price: [1000],
          currency: ['USD']
        }),
        region: [[]],
        sizes: [[]],
        color_names: [[]],
        gender_name: [[]],
        category_name: [[]],
        brand_name: [[]]
      }),
      limit: [10]
    });
  }

  ngOnInit() {
    this.searchForm.valueChanges.pipe(
      debounceTime(300),
      distinctUntilChanged()
    ).subscribe(formValue => {
      this.performSearch(formValue);
    });
  }

  performSearch(searchRequest: SearchRequest) {
    this.searchService.search(searchRequest).subscribe({
      next: (results) => {
        console.log('Search results:', results);
        // Handle the results here
      },
      error: (error) => {
        console.error('Search error:', error);
        // Handle errors here
      }
    });
  }

  clearFilters() {
    const currentQuery = this.searchForm.get('text_query')?.value;
    this.searchForm.reset({
      text_query: currentQuery,
      filters: {
        price: { min_price: 0, max_price: 1000, currency: 'USD' },
        region: [],
        sizes: [],
        color_names: [],
        gender_name: [],
        category_name: [],
        brand_name: []
      },
      limit: 10
    });
  }
}
