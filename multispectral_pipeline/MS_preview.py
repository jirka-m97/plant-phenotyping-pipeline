# =========================================================================
# RGB Camera Preview Application (Python script, en-GB)
# Author: Jiří Mach
# Institution: UCT Prague, Faculty of Food and Biochemical Technology, Laboratory of Bioengineering
# Licence: Apache 2.0
# Date: 2025-09-18
# Description:
#   Provides live RGB preview from a connected camera via the eBUS SDK.
#   The script automatically detects the first available device, opens
#   a stream, configures acquisition parameters, and displays a Bayer-
#   demosaiced RGB preview window using OpenCV. User can exit the preview
#   by pressing any key or closing the window.
# =========================================================================

import os
import cv2
import numpy as np
import eBUS as eb
import PvSampleUtils as psu

BUFFER_COUNT = 16
kb = psu.PvKb()

opencv_is_available = True
try:
    import cv2
    opencv_version = cv2.__version__
except:
    opencv_is_available = False
    print("Warning: OpenCV is required to display preview window.")

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
    print("Connecting to device...")
    result, device = eb.PvDevice.CreateAndConnect(connection_ID)
    if device is None:
        print(f"Unable to connect to device: {result.GetCodeString()} ({result.GetDescription()})")
    return device

def open_stream(device, connection_ID, source_channel):
    print("Opening stream from device...")
    if isinstance(device, eb.PvDeviceGEV):
        stream = eb.PvStreamGEV()
        if stream.Open(connection_ID, 0, source_channel).IsFailure():
            print(f"Error opening source {source_channel} to GigE Vision device")
            return None
    else:
        result, stream = eb.PvStream.CreateAndOpen(connection_ID)
        if stream is None:
            print(f"Unable to stream from device. {result.GetCodeString()} ({result.GetDescription()})")
    return stream

def configure_stream(device, stream, source_channel):
    if isinstance(device, eb.PvDeviceGEV):
        device.NegotiatePacketSize()
        local_ip = stream.GetLocalIPAddress()
        local_port = stream.GetLocalPort()
        device.SetStreamDestination(local_ip, local_port, source_channel)

def configure_stream_buffers(device, stream):
    buffer_list = []
    size = device.GetPayloadSize()
    buffer_count = min(BUFFER_COUNT, stream.GetQueuedBufferMaximum())
    for _ in range(buffer_count):
        buffer = eb.PvBuffer()
        buffer.Alloc(size)
        stream.QueueBuffer(buffer)
        buffer_list.append(buffer)
    print(f"Configured {buffer_count} buffers.")
    return buffer_list

def acquire_preview(device, stream):
    params = device.GetParameters()
    source_selector = params.Get("SourceSelector")
    source_selector.SetValue("Source0")

    acq_mode = params.Get("AcquisitionMode")
    acq_mode.SetValue("Continuous")

    width = params.Get("Width")
    height = params.Get("Height")
    width.SetValue(2048)
    height.SetValue(1536)

    exposure = params.Get("ExposureTime")
    exposure.SetValue(985)  # adjust as needed

    frame_rate = params.Get("AcquisitionFrameRate")
    frame_rate.SetValue(2)

    device.StreamEnable()
    params.Get("AcquisitionStart").Execute()

    print("RGB preview started. Press any key to exit.")

    while True:
        result, pvbuffer, op_result = stream.RetrieveBuffer(1000)
        if result.IsOK() and op_result.IsOK():
            image = pvbuffer.GetImage()
            if image.GetPixelType() == eb.PvPixelBayerRG8:
                img_data = np.frombuffer(image.GetDataPointer(), dtype=np.uint8).reshape(
                    (image.GetHeight(), image.GetWidth())
                )
                img_rgb = cv2.cvtColor(img_data, cv2.COLOR_BayerRG2RGB)

                cv2.namedWindow("RGB Preview", cv2.WINDOW_NORMAL)
                cv2.resizeWindow("RGB Preview", 1280, 960)  # nebo podle potřeby
                cv2.imshow("RGB Preview", img_rgb)
                cv2.waitKey(1)

                if cv2.getWindowProperty("RGB Preview", cv2.WND_PROP_VISIBLE) < 1:
                    break

            stream.QueueBuffer(pvbuffer)

        if kb.kbhit():
            kb.getch()
            break

    params.Get("AcquisitionStop").Execute()
    device.StreamDisable()
    stream.AbortQueuedBuffers()
    while stream.GetQueuedBufferCount() > 0:
        stream.RetrieveBuffer()
    cv2.destroyAllWindows()
    kb.stop()
    print("Preview stopped.")

def main():
    print("Starting RGB preview application...")
    connection_ID = auto_select_first_device()
    if connection_ID:
        device = connect_to_device(connection_ID)
        if device:
            stream = open_stream(device, connection_ID, 0)
            if stream:
                configure_stream(device, stream, 0)
                buffers = configure_stream_buffers(device, stream)
                acquire_preview(device, stream)
                buffers.clear()
                stream.Close()
                eb.PvStream.Free(stream)
            device.Disconnect()
            eb.PvDevice.Free(device)
    print("Program exited.")

if __name__ == "__main__":
    main()
