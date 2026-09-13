import { AppRegistry } from 'react-native';
import App from './App';
import { name as appName } from './app.json';

// Si no existe app.json con name, usamos 'navegolocal'
AppRegistry.registerComponent('main', () => App);

if (window.document) {
  AppRegistry.runApplication('main', {
    rootTag: document.getElementById('root') || document.getElementById('main'),
  });
}
