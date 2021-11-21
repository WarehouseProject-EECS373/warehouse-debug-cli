# Warehouse debug CLI

## Example usage for Zumo debugging

See all messages queued and handled. Enable by compiling the zumo-controller with `-DDEBUG_MODE_ENABLED`. Will slow down the code and timing may be a bit imprecise but this can really help us debug state machine/logic issues.

```
$ python -m wdc.cli
Welcome to warehouse-debug-console
(wdc) connect
(wdc) listen
Starting listener
(wdc) listen
Starting listener
(wdc) dispatch
(wdc) listen stop
(wdc) showlog
[01:45:44.323210]: HEARTBEAT_MSG handled by WATCHDOG
[01:45:44.705814]: SM_DISPATCH_FROM_IDLE queued to STATE
[01:45:44.705943]: SM_DISPATCH_FROM_IDLE handled by STATE
[01:45:44.706028]: DRIVE_ENABLE queued to DRIVE
[01:45:44.706098]: REFARR_CALIBRATE queued to REFARR
[01:45:44.706168]: REFARR_CALIBRATE handled by REFARR
[01:45:44.706238]: DRIVE_TIMED_TURN queued to DRIVE
[01:45:44.706307]: DRIVE_ENABLE handled by DRIVE
[01:45:44.706376]: DRIVE_TIMED_TURN handled by DRIVE
[01:45:44.829331]: HEARTBEAT_MSG queued to WATCHDOG
[01:45:44.830000]: HEARTBEAT_MSG handled by WATCHDOG
[01:45:45.209795]: DRIVE_TIMED_TURN_DONE queued to REFARR
[01:45:45.209884]: DRIVE_TIMED_TURN_DONE queued to DRIVE
[01:45:45.209953]: DRIVE_TIMED_TURN_DONE handled by REFARR
[01:45:45.210028]: DRIVE_TIMED_TURN queued to DRIVE
[01:45:45.210096]: DRIVE_TIMED_TURN_DONE handled by DRIVE
[01:45:45.210252]: DRIVE_TIMED_TURN handled by DRIVE
[01:45:45.332707]: HEARTBEAT_MSG queued to WATCHDOG
[01:45:45.333442]: HEARTBEAT_MSG handled by WATCHDOG
[01:45:45.833274]: HEARTBEAT_MSG queued to WATCHDOG
[01:45:45.833924]: HEARTBEAT_MSG handled by WATCHDOG
[01:45:46.213808]: DRIVE_TIMED_TURN_DONE queued to REFARR
[01:45:46.213888]: DRIVE_TIMED_TURN_DONE queued to DRIVE
[01:45:46.213955]: DRIVE_TIMED_TURN_DONE handled by REFARR
[01:45:46.214030]: DRIVE_TIMED_TURN queued to DRIVE
[01:45:46.214096]: DRIVE_TIMED_TURN_DONE handled by DRIVE
[01:45:46.214169]: DRIVE_TIMED_TURN handled by DRIVE
[01:45:46.336666]: HEARTBEAT_MSG queued to WATCHDOG
[01:45:46.337416]: HEARTBEAT_MSG handled by WATCHDOG
[01:45:46.715811]: DRIVE_TIMED_TURN_DONE queued to REFARR
[01:45:46.715892]: DRIVE_TIMED_TURN_DONE queued to DRIVE
[01:45:46.715962]: DRIVE_TIMED_TURN_DONE handled by REFARR
[01:45:46.716045]: DRIVE_TIMED_TURN_DONE handled by DRIVE
[01:45:46.839330]: HEARTBEAT_MSG queued to WATCHDOG
[01:45:46.840025]: HEARTBEAT_MSG handled by WATCHDOG
(wdc)
```
