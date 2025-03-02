"""This demo shows the latest notification from a connected Apple device on a TFT Gizmo screen.

The A and B buttons on the CircuitPlayground Bluefruit can be used to scroll through all active
notifications.
"""

import board
import digitalio
import displayio
import time

import adafruit_ble
from adafruit_ble.advertising.standard import SolicitServicesAdvertisement
from adafruit_ble.services.apple import AppleNotificationService
from adafruit_display_notification import apple
from adafruit_display_notification import NotificationFree
from adafruit_display_ble_status.advertising import AdvertisingWidget
#from adafruit_circuitplayground import cp
from adafruit_gizmo import tft_gizmo

# This is a whitelist of apps to show notifications from.
#APPS = ["com.tinyspeck.chatlyio", "com.atebits.Tweetie2"]
APPS = []

DELAY_AFTER_PRESS = 15
DEBOUNCE = 0.1

a = digitalio.DigitalInOut(board.BUTTON_A)
a.switch_to_input(pull=digitalio.Pull.DOWN)
b = digitalio.DigitalInOut(board.BUTTON_B)
b.switch_to_input(pull=digitalio.Pull.DOWN)

def find_connection():
    for connection in radio.connections:
        if AppleNotificationService not in connection:
            continue
        if not connection.paired:
            connection.pair()
        return connection, connection[AppleNotificationService]
    return None, None

# Start advertising before messing with the display so that we can connect immediately.
radio = adafruit_ble.BLERadio()
advertisement = SolicitServicesAdvertisement()
advertisement.complete_name = "CIRCUITPY"
advertisement.solicited_services.append(AppleNotificationService)

SCALE = 2

display = tft_gizmo.TFT_Gizmo()
group = displayio.Group(scale=SCALE)
display.show(group)

width = display.width // SCALE
height = display.height // SCALE

radio_widget = AdvertisingWidget("CIRCUITPY", width, height)
group.append(radio_widget)

current_notification = None
all_ids = []
last_press = time.monotonic()
active_connection, notification_service = find_connection()
while True:
    if not active_connection:
        radio.start_advertising(advertisement)

    while not active_connection:
        active_connection, notification_service = find_connection()

    while active_connection.connected:
        all_ids.clear()
        current_notifications = notification_service.active_notifications
        for id in current_notifications:
            notification = current_notifications[id]
            if APPS and notification.app_id not in APPS:
                continue
            all_ids.append(id)

        all_ids.sort(key=lambda x: current_notifications[x]._raw_date)

        if current_notification and current_notification.removed:
            # Stop showing the latest and show that there are no new notifications.
            current_notification = None

        if not current_notification and not all_ids:
            group[0] = NotificationFree(width, height)
        elif all_ids:
            now = time.monotonic()
            if current_notification and current_notification.id in all_ids and now - last_press < DELAY_AFTER_PRESS:
                index = all_ids.index(current_notification.id)
            else:
                index = len(all_ids) - 1
            if now - last_press >= DEBOUNCE:
                if b.value and index > 0:
                    last_press = now
                    index += -1
                if a.value and index < len(all_ids) - 1:
                    last_press = now
                    index += 1

            id = all_ids[index]
            if not current_notification or current_notification.id != id:
                current_notification = current_notifications[id]
                print(current_notification._raw_date, current_notification)
                group[0] = apple.create_notification_widget(current_notification, width, height)

    active_connection = None
    notification_service = None
