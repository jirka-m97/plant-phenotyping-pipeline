"""
camera_control_and_data_acqisitioin.py
--------------------------------------

Author: Jiří Mach 
Acknowledgement: Developed with guidance from JAI Support
Institution: UCT Prague, Faculty of Food and Biochemical Technology,
             Laboratory of Bioengineering
Date: 2025-08-19
License: Apache 2.0

Description:
This script provides automated control and data acquisition for the 
multispectral FS 3200D 10GE camera. It was developed as an alternative 
to the eBUS Player for JAI, which, while functional, presented limitations 
in user-friendliness and process automation. By employing the Pleora eBUS SDK 
(`eBUS`, `PvSampleUtils`), OpenCV (`cv2`), and NumPy (`numpy`), the script 
enables device detection, connection, and dual-stream acquisition from 
the RGB (Source0) and NIR (Source1) sensors.

Core functionality includes:
- Automatic device detection and connection via GigE Vision interface.
- Stream negotiation, packet size optimisation, and buffer allocation.
- Configuration of camera parameters (resolution, exposure time, frame rate, 
  acquisition mode).
- Acquisition of multispectral images with alternating retrieval from RGB and NIR sensors.
- Handling of multiple payload formats, including Pleora-compressed data.
- Saving of raw binary images for subsequent processing (RGB and NIR separately).
- Real-time diagnostic output (frame rate, bandwidth, compression ratio).
- Acquisition of calibration frames (BIAS, DARK, FLAT) for both sensors, 
  required for the generation of MASTER calibration images.

Calibration images:
- BIAS: exposure time 1 µs, lens shuttered (RGB and NIR).
- DARK: exposure times 985 µs (RGB) and 2850 µs (NIR), lens shuttered.
- FLAT: identical exposure settings as DARK, but with lens uncovered.
- For each category, 20 images were acquired at full resolution (2048 × 1536 px),
  consistent with object images (plants).

Usage:
- Requires Python 3.x, Pleora eBUS SDK, OpenCV, and NumPy.
- Output data are saved in `.bin` format for subsequent analysis.
- Designed for automated, reproducible dual-channel multispectral imaging workflows.

Notes:
Ensure that the Pleora eBUS SDK and drivers are correctly installed on the 
host system prior to execution.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""

import os
import cv2
import numpy as np
import eBUS as eb
import PvSampleUtils as psu

BUFFER_COUNT = 16
IMAGES_PATH = r".\_testing"

frame_count_setting = 1 
# frame_count_setting = 20 # for BIAS, DARK, FLAT

kb = psu.PvKb()

opencv_is_available = True
try:
    # Detect if OpenCV is available
    import cv2

    opencv_version = cv2.__version__
except:
    opencv_is_available = False
    print("Warning: This sample requires python3-opencv to display a window")

def auto_select_first_device():
    finder = eb.PvSystem()
    finder.Find()  # Aktualizuje seznam zařízení
    count = finder.GetInterfaceCount()
    for i in range(count):
        interface = finder.GetInterface(i)
        if interface is None:
            continue
        device_count = interface.GetDeviceCount()
        for j in range(device_count):
            device_info = interface.GetDeviceInfo(j)
            if device_info is not None:
                return device_info.GetConnectionID()
    return None

def connect_to_device(connection_ID):
    # Connect to the GigE Vision or USB3 Vision device
    print("Connecting to device.")
    result, device = eb.PvDevice.CreateAndConnect(connection_ID)
    if device is None:
        print(
            f"Unable to connect to device: {result.GetCodeString()} ({result.GetDescription()})"
        )
    return device


def open_stream(device, connection_ID, source_channel):
    # Open stream from the GigE Vision or USB3 Vision device
    print("Opening stream from device.")
    
    if isinstance(device, eb.PvDeviceGEV):
        stream = eb.PvStreamGEV()
        if stream.Open(connection_ID, 0, source_channel).IsFailure():
            print("\tError opening source", str(source_channel), " to GigE Vision device")
            return False
    else:
        result, stream = eb.PvStream.CreateAndOpen(connection_ID)
        if stream is None:
            print(
                f"Unable to stream from device. {result.GetCodeString()} ({result.GetDescription()})"
            )
    return stream


def configure_stream(device, stream, source_channel):


    if isinstance(device, eb.PvDeviceGEV):
        # Negotiate packet size
        device.NegotiatePacketSize()
        # Configure device streaming destination
        device.GetDefaultGenICamXMLFilename()
        local_ip = stream.GetLocalIPAddress()
        local_port = stream.GetLocalPort()

        print(
            "\tSetting source destination on device (channel",
            source_channel,
            ") to",
            local_ip,
            "port",
            local_port,
        )
        device.SetStreamDestination(stream.GetLocalIPAddress(), stream.GetLocalPort(), source_channel)


def configure_stream_buffers(device, stream):
    buffer_list = []
    # Read payload size from device
    size = device.GetPayloadSize()

    # Use BUFFER_COUNT or the stream's max buffer count, whichever is smaller
    buffer_count = stream.GetQueuedBufferMaximum()
    if buffer_count > BUFFER_COUNT:
        buffer_count = BUFFER_COUNT

    # Allocate buffers
    for i in range(buffer_count):
        pvbuffer = eb.PvBuffer()
        pvbuffer.Alloc(size)
        buffer_list.append(pvbuffer)

    # Queue all buffers in the stream
    for pvbuffer in buffer_list:
        stream.QueueBuffer(pvbuffer)
    print(f"Created {buffer_count} buffers")
    return buffer_list


def save_image_RGB(image_data, images_path, frame_count):
    image_name = f"Img_{frame_count + 1}_RGB.bin"
    with open(os.path.join(images_path, image_name), "wb") as f:
        f.write(image_data.tobytes())  # Save as raw binary data
    print("Saved RGB image:", image_name)


def save_image_NIR(image_data, images_path, frame_count):
    image_name = f"Img_{frame_count + 1}_NIR.bin"
    with open(os.path.join(images_path, image_name), "wb") as f:
        f.write(image_data.tobytes())  # Save as raw binary data
    print("Saved RGB image:", image_name)


def dashed_line():
    print(50 * "-")


def acquire_images(device, source0, source1, images_path):
    device_params = device.GetParameters()

    width = device_params.Get("Width")
    width.SetValue(2048) 
    height = device_params.Get("Height")
    height.SetValue(1536)
    print("Width:", width.GetValue()[1])
    print("Height:", height.GetValue()[1])

    # Print available sensors
    source_selector = device_params.Get("SourceSelector")
    result, num_entries = source_selector.GetEntriesCount()
    if result.IsFailure():
        print("Error retrieving sensor count")
        return
    print(f"Number of available sensors: {num_entries}")

    for i in range(num_entries):
        result, entry = source_selector.GetEntryByIndex(i)
        if result.IsFailure():
            print(f"Error retrieving sensor entry at index {i}")
            continue
        result, sensor_name = entry.GetName()
        result, sensor_value = entry.GetValue()
        if result.IsFailure():
            print(f"Error retrieving value for sensor {sensor_name}")
            continue
        print(f"Sensor name: {sensor_name} -- value: {sensor_value}")

    # Configure sensors - Source0 (RGB) and Source1 (NIR)
    source_selector.SetValue("Source0")
    source0_exp_time = device_params.Get("ExposureTime")
    source0_exp_time.SetValue(985) # for DARK, FLAT, plant imaging
    # source0_exp_time.SetValue(1) # for BIAS
    print(f"Source_0_exp_time: {source0_exp_time.GetValue()[1]} us")
  
    # Set AcquisitionFrameRate
    acq_frame_rate = device_params.Get("AcquisitionFrameRate")
    acq_frame_rate.SetValue(2)  # in Hz

    # Acquisition mode
    acq_mode = device_params.Get("AcquisitionMode")
    acq_mode.SetValue("MultiFrame")

    # Set number of frames for MultiFrame mode
    acq_frame_count = device_params.Get("AcquisitionFrameCount")
    acq_frame_count.SetValue(frame_count_setting)


    source_selector.SetValue("Source1")
    source1_exp_time = device_params.Get("ExposureTime")
    source1_exp_time.SetValue(2850) # for DARK, FLAT, plant imaging
    # source1_exp_time.SetValue(1) # for BIAS
    print(f"Source_1_exp_time: {source1_exp_time.GetValue()[1]} us")
    print("RGB and NIR sensors configured.")

    # Set AcquisitionFrameRate
    acq_frame_rate = device_params.Get("AcquisitionFrameRate")
    acq_frame_rate.SetValue(2)  # in Hz

    # Acquisition mode
    acq_mode = device_params.Get("AcquisitionMode")
    acq_mode.SetValue("MultiFrame")

    # Get stream parameters
    stream_params = source0.GetParameters()
    
    frame_rate = stream_params.Get("AcquisitionRate")
    bandwidth = stream_params["Bandwidth"]

    # Start acquisition
    print("Enabling streaming and sending AcquisitionStart command.")
    source_selector.SetValue("Source0")
    device.StreamEnable()
    result = device_params.Get("AcquisitionStart").Execute()
    source_selector.SetValue("Source1")
    device.StreamEnable()
    result = device_params.Get("AcquisitionStart").Execute()

    doodle = "|\\-|-/"  # animation spinner
    doodle_index = 0
    display_image = False
    warning_issued = False
    errors = 0
    decompression_filter = eb.PvDecompressionFilter()

    frame_count = 0
    max_frames = acq_frame_count.GetValue()[1]
    recieived_frames_for_source = 0
    while frame_count < max_frames:
        result, pvbuffer, operational_result = None, None, None
        # Retrieve buffer from the correct source
        if recieived_frames_for_source == 0:
            result, pvbuffer, operational_result = source0.RetrieveBuffer(1000)
            if not result.IsOK():
                print(f"source{recieived_frames_for_source} {result.GetCodeString()}")
            # Have to receive Source1 as well, otherwise buffer will fill up
            result_trash, pvbuffer_trash, operational_result_trash = source1.RetrieveBuffer(1000)
            # release the trash buffer
            if result_trash.IsOK():
                source1.QueueBuffer(pvbuffer_trash)
        else:
            result, pvbuffer, operational_result = source1.RetrieveBuffer(1000)
            if not result.IsOK():
                print(f"source{recieived_frames_for_source} {result.GetCodeString()}")
            # Have to receive Source1 as well, otherwise buffer will fill up
            result_trash, pvbuffer_trash, operational_result_trash = source0.RetrieveBuffer(1000)
            # release the trash buffer
            if result_trash.IsOK():
                source0.QueueBuffer(pvbuffer_trash)

        if result.IsOK():
            if operational_result.IsOK():
                result, frame_rate_val = frame_rate.GetValue()
                result, bandwidth_val = bandwidth.GetValue()

                print(
                    f"{doodle[doodle_index]} ImgID: {pvbuffer.GetBlockID():03d}"
                )

                image = None
                payload_type = pvbuffer.GetPayloadType()
                # Process based on payload type
                if payload_type == eb.PvPayloadTypeImage:
                    image = pvbuffer.GetImage()
                elif payload_type == eb.PvPayloadTypeChunkData:
                    print(f" Chunk Data with {pvbuffer.GetChunkCount()} chunks")
                elif payload_type == eb.PvPayloadTypeRawData:
                    print(
                        f" Raw Data: {pvbuffer.GetRawData().GetPayloadLength()} bytes")
                elif payload_type == eb.PvPayloadTypeMultiPart:
                    print(
                        f" Multi Part with {pvbuffer.GetMultiPartContainer().GetPartCount()} parts")
                elif payload_type == eb.PvPayloadTypePleoraCompressed:
                    if eb.PvDecompressionFilter.IsCompressed(pvbuffer):
                        result, pixel_type, width, height = (
                            eb.PvDecompressionFilter.GetOutputFormatFor(pvbuffer)
                        )
                        if result.IsOK():
                            calculated_size = (
                                eb.PvImage.GetPixelSize(pixel_type) * width * height / 8
                            )
                            out_buffer = eb.PvBuffer()
                            result, decompressed_buffer = decompression_filter.Execute(
                                pvbuffer, out_buffer
                            )
                            image = decompressed_buffer.GetImage()
                            if result.IsOK():
                                decompressed_size = decompressed_buffer.GetSize()
                                compression_ratio = (
                                    decompressed_size / pvbuffer.GetAcquiredSize()
                                )
                                if calculated_size != decompressed_size:
                                    errors += 1
                                print(
                                    f" Compression ratio: {'{0:.2f}'.format(compression_ratio)} Errors: {errors}")
                            else:
                                print(
                                    " Could not decompress (Pleora compressed)")
                                errors += 1
                        else:
                            print(" Could not read header (Pleora compressed)")
                            errors += 1
                    else:
                        print(" Not matching compressed format")
                        errors += 1
                else:
                    print(" Unsupported payload type")

                if image:
                    print(f"  W: {image.GetWidth()} H: {image.GetHeight()} ")
                    image_data = image.GetDataPointer()

                    # OpenCV image display
                    if opencv_is_available:
                        if image.GetPixelType() == eb.PvPixelMono8:
                            display_image = True
                            save_image_NIR(image_data, images_path, frame_count)
                        elif image.GetPixelType() == eb.PvPixelRGB8:
                            display_image = True
                            image_array = np.array(image_data, dtype=np.uint8).reshape(
                                (image.GetHeight(), image.GetWidth(), 3)
                            )
                            image_array = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
                        elif image.GetPixelType() == eb.PvPixelBayerRG8:
                            save_image_RGB(image_data, images_path, frame_count)
                            image_data = cv2.cvtColor(image_data, cv2.COLOR_BayerBG2RGB)
                        else:
                            if not warning_issued:
                                print(
                                    "\nCurrently only Mono8 / RGB8 images are displayed\n",
                                    end="",
                                )
                                warning_issued = True

                print(
                    f" {frame_rate_val:.1f} FPS  {bandwidth_val / 1e6:.1f} Mb/s     ",
                    end="\r",
                )
            else:
                print(
                    f"{doodle[doodle_index]} {operational_result.GetCodeString()}")
            # Queue the buffer back to the to the correct stream
            if recieived_frames_for_source == 0:
                source0.QueueBuffer(pvbuffer)
            else:
                source1.QueueBuffer(pvbuffer)

        else:
            print(f"source{recieived_frames_for_source} {result.GetCodeString()}")

        doodle_index = (doodle_index + 1) % 6
        if kb.kbhit():
            kb.getch()
            break

        #Switch sensor after each frame
        if frame_count % 2 == 0:
            print("Switching to Source1 (NIR)")
            recieived_frames_for_source = 1
            #source_selector.SetValue("Source1")
        else:
            print("Switching to Source0 (RGB)")
            recieived_frames_for_source = 0
            #source_selector.SetValue("Source0")

        frame_count += 1

    frame_count = 0
    max_frames = frame_count_setting  # Number of RGB+NIR image pairs
    source_selector.SetValue("Source0")
    device_params.Get("AcquisitionStart").Execute()
    source_selector.SetValue("Source1")
    device_params.Get("AcquisitionStart").Execute()

    for i in range(max_frames):
        # === RGB image ===
        result_rgb, pvbuffer_rgb, operational_result_rgb = source0.RetrieveBuffer(1000)
        result_nir, pvbuffer_nir, operational_result_nir = source1.RetrieveBuffer(1000)

        if result_rgb.IsOK() and operational_result_rgb.IsOK():
            image = pvbuffer_rgb.GetImage()
            if image and image.GetPixelType() == eb.PvPixelBayerRG8:
                image_data = image.GetDataPointer()
                save_image_RGB(image_data, images_path, i)
                #print(f"Saved RGB image: Img_{i}_RGB.bin")
            source0.QueueBuffer(pvbuffer_rgb)
        else:
            print(f"source0 {result_rgb.GetCodeString()}")

        # === NIR image ===
        if result_nir.IsOK() and operational_result_nir.IsOK():
            image = pvbuffer_nir.GetImage()
            if image and image.GetPixelType() == eb.PvPixelMono8:
                image_data = image.GetDataPointer()
                save_image_NIR(image_data, images_path, i)
                #print(f"Saved NIR image: Img_{i}_NIR.bin")
            source1.QueueBuffer(pvbuffer_nir)
        else:
            print(f"source0 {result_rgb.GetCodeString()}")

    source_selector.SetValue("Source0")
    device_params.Get("AcquisitionStop").Execute()
    source_selector.SetValue("Source1")
    device_params.Get("AcquisitionStop").Execute()

    kb.stop()

    print("\nSending AcquisitionStop command to the device")

    print("Disabling streaming on the controller.")
    device.StreamDisable()

    print("Aborting remaining buffers in stream")
    source0.AbortQueuedBuffers()
    while source0.GetQueuedBufferCount() > 0:
        result, pvbuffer, op_result = source0.RetrieveBuffer()
    source1.AbortQueuedBuffers()
    while source1.GetQueuedBufferCount() > 0:
        result, pvbuffer, op_result = source1.RetrieveBuffer()


print("MS analysis process has started")

connection_ID = auto_select_first_device()
if connection_ID:
    device = connect_to_device(connection_ID)
    if device:
        stream1 = open_stream(device, connection_ID, 0)
        stream2 = open_stream(device, connection_ID, 1)

        if stream1 and stream2:
            configure_stream(device, stream2, 1)
            configure_stream(device, stream1, 0)

            buffer_list1 = configure_stream_buffers(device, stream1)
            buffer_list2 = configure_stream_buffers(device, stream2)
            acquire_images(
                device, stream1, stream2, images_path=IMAGES_PATH
            )
            buffer_list1.clear()
            buffer_list2.clear()

            print("Closing stream")
            stream1.Close()
            stream2.Close()
            eb.PvStream.Free(stream1)
            eb.PvStream.Free(stream2)

        print("Disconnecting device")
        device.Disconnect()
        eb.PvDevice.Free(device)

print("Process successfully completed. Exiting program...")
