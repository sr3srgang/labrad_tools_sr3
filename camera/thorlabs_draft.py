import numpy as np
from thorlabs_tsi_sdk.tl_camera import TLCameraSDK
from thorlabs_tsi_sdk.tl_camera_enums import OPERATION_MODE
NUM_FRAMES = 10

with TLCameraSDK() as sdk:
	avail_cam = sdk.discover_available_cameras()
	if len(avail_cam) < 1:
		print("no cam detected")
	else:
		print(avail_cam)
		
	cam = avail_cam[0]
	with sdk.open_camera(cam) as camera:
		camera.frames_per_trigger_zero_for_unlimited = 1
		camera.operation_mode = OPERATION_MODE.SOFTWARE_TRIGGERED#HARDWARE_TRIGGERED#BULB
		camera.image_poll_timeout_ms = 2000  # 2 second timeout
		camera.arm(1)
		camera.issue_software_trigger()
		frame = camera.get_pending_frame_or_null()
		print(frame is not None)

