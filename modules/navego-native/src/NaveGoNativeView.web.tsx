import * as React from 'react';

import { NaveGoNativeViewProps } from './NaveGoNative.types';

export default function NaveGoNativeView(props: NaveGoNativeViewProps) {
  return (
    <div>
      <iframe
        style={{ flex: 1 }}
        src={props.url}
        onLoad={() => props.onLoad({ nativeEvent: { url: props.url } })}
      />
    </div>
  );
}
