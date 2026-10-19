// Reexport the native module. On web, it will be resolved to NaveGoNativeModule.web.ts
// and on native platforms to NaveGoNativeModule.ts
export { default } from './src/NaveGoNativeModule';
export { default as NaveGoNativeView } from './src/NaveGoNativeView';
export * from  './src/NaveGoNative.types';
