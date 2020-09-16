import datetime
import sounddevice as sd
import soundfile as sf

filename = 'alarm_sound.wav'

data, sample_rate = sf.read(filename, dtype='float32')


def main():
    valid_user_input = False
    print('Please set an alarm time.')
    while not valid_user_input:
        time = input('(HH:MM): ')
        try:
            time_hour = int(time[:2])
            time_minute = int(time[3:])
            if 0 <= time_hour <= 23 and 0 <= time_minute <= 59 and len(time) == 5:
                valid_user_input = True
            else:
                print('Please enter a valid alarm time')
        except ValueError:
            print('Please enter a valid alarm time')

    alarm_time = datetime.time(time_hour, time_minute)
    print('Alarm set for', time)

    alarm_activate = False
    while not alarm_activate:
        sd.sleep(1)
        time_now = datetime.datetime.now()
        alarm_activate = time_now.hour == alarm_time.hour and time_now.minute == alarm_time.minute

    sd.play(data, sample_rate, loop=True)

    user_input = 'play'
    while user_input == 'play':
        user_input = input('Press Enter to stop.')

    sd.stop()


while True:
    main()
