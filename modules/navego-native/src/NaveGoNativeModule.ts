import { NativeModule, requireNativeModule } from 'expo';

import { NaveGoNativeModuleEvents } from './NaveGoNative.types';

declare class NaveGoNativeModule extends NativeModule<NaveGoNativeModuleEvents> {
  PI: number;
  hello(): string;
  setValueAsync(value: string): Promise<void>;
}

// This call loads the native module object from the JSI.
export default requireNativeModule<NaveGoNativeModule>('NaveGoNative');
