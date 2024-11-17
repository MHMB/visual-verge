import {Component} from '@angular/core';
import {NavBarComponent} from './nav-bar/nav-bar.component'
@Component({
  selector: 'app-root',
  standalone: true,
  imports: [NavBarComponent],
  template: `
    <main>
      <header class="brand-name">
        <img class="brand-logo" src="/assets/logo.svg" alt="logo" aria-hidden="true" />
      </header>
      <section class="content">
        <app-nav-bar></app-nav-bar>
      </section>
    </main>
  `,
  styleUrls: ['./app.component.css'],
})
export class AppComponent {
  title = 'homes';
}