import {Routes} from '@angular/router';
import {NavBarComponent} from './nav-bar/nav-bar.component';
import {DetailsComponent} from './details/details.component';
const routeConfig: Routes = [
  {
    path: '',
    component: NavBarComponent,
    title: 'Home page',
  },
  {
    path: 'details/:id',
    component: DetailsComponent,
    title: 'Home details',
  },
];
export default routeConfig;