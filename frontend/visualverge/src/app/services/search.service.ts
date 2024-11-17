// src/app/services/search.service.ts

import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { SearchRequest } from '../types/search.types';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class SearchService {
  private apiUrl = environment.apiUrl + '/search'; // We'll add this to environment later

  constructor(private http: HttpClient) {}

  search(request: SearchRequest): Observable<any> {
    return this.http.post<any>(this.apiUrl, request);
  }
}
