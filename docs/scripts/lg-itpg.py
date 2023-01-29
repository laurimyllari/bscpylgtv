import asyncio
import math
import sys
from bscpylgtv import WebOsClient
from lg_constants import DB_PATH, LG_IP

screen_resolution = (3840, 2160)
bfi_interval = 0.5
patch_size = 5
rgb_range = "limited"
rgb_min_max = {
        "full": (0, 1023),
        "limited": (64, 940),
        }

async def get_window_properties(screen_resolution, patch_size):
    ratio = screen_resolution[0] / screen_resolution[1]
    area = screen_resolution[0] * screen_resolution[1] * patch_size / 100
    height = int(round(math.sqrt(area/ratio)))
    width = int(round(height * ratio))
    startx = int(round(screen_resolution[0] / 2 - width / 2))
    starty = int(round(screen_resolution[1] / 2 - height / 2))
    window = {'width': width, 'height': height, 'startx': startx, 'starty': starty}

    if patch_size < 100:
        print(f"patch window: {window}")

    return window


async def display_patch(client, patch, bfi_interval, window_full, window_patch):
    """ Display full screen black window in the background and color patch window on top of it
    in the given window size. The complete new state should always be set for both."""

    if bfi_interval:
        print("BFI")
        # Set full screen black window in the background again
        await client.set_itpg_patch_window(r=0, b=0, g=0, win_id=0, width=window_full['width'], height=window_full['height'], startx=window_full['startx'], starty=window_full['starty'])
        await client.toggle_itpg(enable=True, numOfBox=1)
        await asyncio.sleep(bfi_interval)

    print(f"patch: {patch}")
    await client.set_itpg_patch_window(r=int(patch[1]), g=int(patch[2]), b=int(patch[3]), win_id=1, width=window_patch['width'], height=window_patch['height'], startx=window_patch['startx'], starty=window_patch['starty'])
    await client.set_itpg_patch_window(r=0, b=0, g=0, win_id=0, width=window_full['width'], height=window_full['height'], startx=window_full['startx'], starty=window_full['starty'])

    await client.toggle_itpg(enable=True, numOfBox=2)


def rgb_float_to_10bit(value):
    (rgb_min, rgb_max) = rgb_min_max[rgb_range]
    return value * (rgb_max - rgb_min) + rgb_min

async def runloop(screen_resolution, bfi_interval, patch_size, rgb_range):
    # Get command line arguments
    if sys.argv[1] == "off":
        print("disable tpg")
        # Connect to WebOS
        client = await WebOsClient.create(LG_IP, states=[], key_file_path=DB_PATH)
        await client.connect()
        # Disable patch windows
        await client.toggle_itpg(enable=False, numOfBox=0)
        # Disconnect WebOS
        await client.disconnect()
        return

    (r8, g8, b8, rf, gf, bf) = sys.argv[1:]
    # convert float rgb values to 10bit int according to rgb_range
    patch = [ f"{rf}, {gf}, {bf}" ] + [ rgb_float_to_10bit(float(x)) for x in (rf, gf, bf) ]

    # Connect to WebOS
    client = await WebOsClient.create(LG_IP, states=[], key_file_path=DB_PATH)
    await client.connect()

    # Get full and patch window properties
    window_full = await get_window_properties(screen_resolution, 100)
    window_patch = await get_window_properties(screen_resolution, patch_size)

    # Display background window and color patch window on top of it
    await display_patch(client, patch, bfi_interval, window_full, window_patch)

    # Disconnect WebOS
    await client.disconnect()

asyncio.run(runloop(screen_resolution, bfi_interval, patch_size, rgb_range))
