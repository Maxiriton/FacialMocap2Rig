# Facial Mocap Data to any rig in blender

This blender extension allows user to transfer facial motion capture data captured by Google's Mediapipe or Apple's ARkit to any blender rig. Instead of having animated shape keys, animation is stored on the rig and is easier to control and adjust to cleanup the mocap animation. 

## Installation

Download this repo as a zip file and drag and drop it into Blender. You'll need at least Blender 5.0.1 for this extension to work. 


## 1. Setup your rig

The main idea of this extension is to record a pose of the rig for each shape key that you recorded at the mocap stage, either with mediapipe or ARkit.

### 1.1 Rigify

If you use a Rigify Rig, then you simply have to load the json setup file provided in the presets folder of this extension. 

![Load Json Preset](https://raw.githubusercontent.com/Maxiriton/images_repo/refs/heads/main/facialmocap2rig/load_json_preset.jpg)

### 1.2 Your own facial rig

If you use your own facial rig, you'll need to record each pose for each shape key defined by ARKit or mediapipe. Load a csv of the animation data to build the list of shape key defined by the mocap process.

![Create list from CSV](https://raw.githubusercontent.com/Maxiriton/images_repo/refs/heads/main/facialmocap2rig/fill_list_from_csv.jpg)

A list of shape keys will appear in the list, you now have to record them one by one. Simply it the record button, pose your rig to match the shape as described in [this page](https://pooyadeperson.com/the-ultimate-guide-to-creating-arkits-52-facial-blendshapes/) and when you are done, hit the Finish Recording Button. Repeat the operation  for each shape key.

The extension comes with a little helper that can symetrize a pose. Click a pose that ends by **Left** or **Right** and click the "symetrize Shape Key" operator below the list. It will automatically symetrize the pose along the X axis. To have this operator work correctly, you need to follow Blender's naming convention for symmetrical bones using **.r** or **.l** in your bones names. 

Once you are done, you can store the configuration in a json file to easily load on other scenes. 

### Multiplier setup

For each shape key, you can setup a custom multiplier to adjust the power of the recorded shape key in the csv file. To do so, simply click on the button at the right of the row and enter the multiplier value. To reset the multiplier, enter a value of **1.0**.

## 2 Apply mocap animation

