import {
  createNaveGoOrientationCore,
} from './NaveGoOrientationCore';

const orientationCore =
  createNaveGoOrientationCore({
    updateIntervalMs: 50,
    magnetometerCorrection: 0.05,
  });

orientationCore.subscribe((state) => {
  console.log(
    '[NOC]',
    JSON.stringify({
      magneticHeading:
        state.magneticHeading !== null
          ? Number(
              state.magneticHeading.toFixed(1)
            )
          : null,

      smoothedHeading:
        state.smoothedHeading !== null
          ? Number(
              state.smoothedHeading.toFixed(1)
            )
          : null,

      accuracy:
        state.headingAccuracy !== null
          ? Number(
              state.headingAccuracy.toFixed(1)
            )
          : null,

      confidence:
        state.confidence,

      field:
        state.magneticFieldStrength !== null
          ? Number(
              state.magneticFieldStrength.toFixed(1)
            )
          : null,

      calibrated:
        state.calibrated,
    })
  );
});

export async function startOrientationTest() {
  await orientationCore.start();

  console.log(
    '[NOC] Orientation Core iniciado'
  );
}

export function stopOrientationTest() {
  orientationCore.stop();

  console.log(
    '[NOC] Orientation Core detenido'
  );
}

