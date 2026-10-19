import { requireNativeView } from 'expo';
import * as React from 'react';

import { NaveGoNativeViewProps } from './NaveGoNative.types';

const NativeView: React.ComponentType<NaveGoNativeViewProps> =
  requireNativeView('NaveGoNative');

export default function NaveGoNativeView(props: NaveGoNativeViewProps) {
  return <NativeView {...props} />;
}
