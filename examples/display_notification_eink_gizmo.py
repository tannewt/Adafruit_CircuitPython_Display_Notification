"""This demo shows the latest notification from a connected Apple device on the EInk screen."""

import board
import displayio
import terminalio
import time

import adafruit_ble
from adafruit_ble.advertising.standard import SolicitServicesAdvertisement
from adafruit_ble.services.apple import AppleNotificationService
from adafruit_display_notification import apple
from adafruit_display_notification import NotificationFree
from adafruit_display_ble_status.advertising import AdvertisingWidget
from adafruit_gizmo import eink_gizmo

# This is a whitelist of apps to show notifications from.
APPS = ["com.tinyspeck.chatlyio", "com.atebits.Tweetie2"]

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
a = SolicitServicesAdvertisement()
a.complete_name = "CIRCUITPY"
a.solicited_services.append(AppleNotificationService)

display = eink_gizmo.EInk_Gizmo()

radio_widget = AdvertisingWidget("CIRCUITPY", display.width, display.height)
display.show(radio_widget)

# True when the screen reflects our current state.
screen_updated = False
latest_notification = None
active_connection, notification_service = find_connection()
while True:
    if not active_connection:
        radio.start_advertising(a)
        screen_updated = False

    while not active_connection:
        active_connection, notification_service = find_connection()

        if not screen_updated and display.time_to_refresh == 0:
            display.refresh()
            screen_updated = True

    while active_connection.connected:
        remaining_time = 600
        if not screen_updated:
            remaining_time = display.time_to_refresh
        new_notification = None
        for notification in notification_service.wait_for_new_notifications(remaining_time):
            # Filter notifications we don't care about.
            if APPS and notification.app_id not in APPS:
                continue
            # Ignore notifications older than the currently shown one.
            if latest_notification and notification._raw_date < latest_notification._raw_date:
                continue
            new_notification = notification
            break

        if new_notification:
            print(new_notification)
            latest_notification = new_notification
            screen_updated = False
            display.show(apple.create_notification_widget(latest_notification, display.width, display.height))
        elif latest_notification and latest_notification.removed:
            # Stop showing the latest and show that there are no new notifications.
            latest_notification = None
            screen_updated = False
            display.show(NotificationFree())

        # Do not refresh the screen more often than every 180 seconds for eInk displays! Rapid refreshes
        # will damage the panel.
        if not screen_updated and display.time_to_refresh == 0:
            display.refresh()
            screen_updated = True

    active_connection = None
    notification_service = None
