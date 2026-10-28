import winsound
import threading
import platform

class SafetyAlarm:
    def __init__(self):
        self.system = platform.system()

    def trigger_alarm_sync(self, frequency=2500, duration=800):
        """Triggers a synchronous local speaker beep or warning tone."""
        try:
            if self.system == "Windows":
                winsound.Beep(frequency, duration)
            else:
                print("\a") # Terminal bell fallback for Linux/Mac
        except Exception as e:
            print(f"Audio alarm trigger error: {e}")

    def trigger_alarm_async(self):
        """Triggers the alarm asynchronously so it doesn't freeze camera frame processing."""
        threading.Thread(target=self.trigger_alarm_sync, daemon=True).start()

if __name__ == "__main__":
    alarm = SafetyAlarm()
    print("Testing safety buzzer...")
    alarm.trigger_alarm_sync(2000, 500)