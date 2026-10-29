export function enableCameraControls(viewer) {
  const controller = viewer.scene.screenSpaceCameraController;
  controller.enableRotate = true;
  controller.enableZoom = true;
  controller.enableTilt = true;
  controller.enableLook = true;
  controller.enableTranslate = true;
}
