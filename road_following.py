#
#
#First, create the model. This must match the model used in the interactive training notebook.
import torch
import torchvision

CATEGORIES = ['apex']

device = torch.device('cuda')
model = torchvision.models.resnet18(pretrained=False)
model.fc = torch.nn.Linear(512, 2 * len(CATEGORIES))
model = model.cuda().eval().half()
#
#Next, load the saved model.  Enter the model path you used to save.
model.load_state_dict(torch.load('road_following_model.pth'))
#
#Convert and optimize the model using torch2trt for faster inference with TensorRT. Please see the torch2trt readme for more details.
#This optimization process can take a couple minutes to complete.
from torch2trt import torch2trt

data = torch.zeros((1, 3, 224, 224)).cuda().half()

model_trt = torch2trt(model, [data], fp16_mode=True)
#
#Save the optimized model using the cell below
torch.save(model_trt.state_dict(), 'road_following_model_trt.pth')
#
#Load the optimized model by executing the cell below
import torch
from torch2trt import TRTModule

model_trt = TRTModule()
model_trt.load_state_dict(torch.load('road_following_model_trt.pth'))
#
#Create the racecar class
#
from jetracer.nvidia_racecar import NvidiaRacecar

car = NvidiaRacecar()
#
#Create the camera class.
from jetcam.csi_camera import CSICamera

camera = CSICamera(width=224, height=224, capture_fps=65)
"""
Finally, execute the cell below to make the racecar move forward, steering the racecar based on the x value of the apex.

Here are some tips,

If the car wobbles left and right, lower the steering gain
If the car misses turns, raise the steering gain
If the car tends right, make the steering bias more negative (in small increments like -0.05)
If the car tends left, make the steering bias more postive (in small increments +0.05)
"""
from utils import preprocess
import numpy as np

STEERING_GAIN = 0.75
STEERING_BIAS = 0.00

car.throttle = 0.15

while True:
    image = camera.read()
    image = preprocess(image).half()
    output = model_trt(image).detach().cpu().numpy().flatten()
    x = float(output[0])
    car.steering = x * STEERING_GAIN + STEERING_BIAS
    