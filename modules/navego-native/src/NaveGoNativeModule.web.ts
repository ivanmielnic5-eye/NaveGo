import { registerWebModule, NativeModule } from 'expo';

import { ChangeEventPayload } from './NaveGoNative.types';

type NaveGoNativeModuleEvents = {
  onChange: (params: ChangeEventPayload) => void;
}

class NaveGoNativeModule extends NativeModule<NaveGoNativeModuleEvents> {
  PI = Math.PI;
  async setValueAsync(value: string): Promise<void> {
    this.emit('onChange', { value });
  }
  hello() {
    return 'Hello world! 👋';
  }
};

export default registerWebModule(NaveGoNativeModule, 'NaveGoNativeModule');
