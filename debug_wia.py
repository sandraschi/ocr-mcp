import logging
import platform
import sys
import comtypes
import comtypes.client as cc
import pythoncom
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WIA_DEBUG")

def test_wia():
    print(f"Platform: {platform.system()}")
    print(f"Python: {sys.version}")

    try:
        pythoncom.CoInitialize()
        print("COM Initialized")
        
        print("Attempting to create WIA.DeviceManager...")
        # Try to create without pre-generated WIALib first to see if it triggers generation
        wia_manager = cc.CreateObject("WIA.DeviceManager")
        print("WIA DeviceManager created successfully")
        
        print(f"DeviceCount: {wia_manager.DeviceInfos.Count}")
        
        if wia_manager.DeviceInfos.Count == 0:
            print("No devices found in DeviceInfos.")
            return

        for i, info in enumerate(wia_manager.DeviceInfos):
            print(f"\n--- Device {i+1} ---")
            try:
                # Property 2 is "Name", 3 is "Description"
                # But let's try to access Properties collection
                for prop in info.Properties:
                    print(f"  {prop.Name}: {prop.Value}")
                
                print("Attempting to connect...")
                device = info.Connect()
                print("Successfully connected to device")
                
                print("Retrieving items...")
                items = device.GetItems()
                print(f"Items found: {len(items)}")
                
            except Exception as e:
                print(f"  FAILED to interact with device: {e}")

    except Exception as e:
        print(f"GLOBAL ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pythoncom.CoUninitialize()

if __name__ == "__main__":
    test_wia()
