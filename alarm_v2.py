# Bugs:
# currently the alarm tone will have to play to the end of its current loop to turn off

# future features:
# timer_objects still display their time as (5:30:0) instead of (05:30:00)
# add in a way for the program to read/write alarms on startup and close.
# make it so that you can enter a short format for timers, with it prioritising seconds, then minutes, then hours
# do the same for alarms, but prioritise hours, then minutes, then seconds
# add a way to delete all timing objects
# when I add more alarm tones, I should display them to the user when asking him to select one

# some general inconsistancies in the code, namely in the way prints, inputs and new_liens are handled, can still be cleaned up

#log:
# alarms/timers will now be deleting if they are not recurring, and should have been activated while another alarm went off

import datetime
import threading
from time import sleep
from playsound import playsound
from math import floor

check_delay = 0.8					# delay between datetime.now() checks
lifetime_objects_count = 0		# keeps count of how many objects have been made - used for object naming
timing_objects_ls = []			# stores all active alarms and timers
exit_flag = False
alarm_flag = False


class TimingObject():
	alarm_tones = {
	'basic': 'alarm_sound.wav'
	}

	def __init__(self, alarm_tone='basic'):
		global lifetime_objects_count
		global timing_objects_ls
		self.alarm_tone = alarm_tone
		if self.alarm_tone not in self.alarm_tones.keys():
			self.alarm_tone = 'basic'
		lifetime_objects_count += 1
		timing_objects_ls.append(self)

	def __len__(self):
		return lifetime_objects_count

	def __repr__(self):
		return f"{self.name} - {self.hour}:{self.minute}:{self.second}, alarm_tone={self.alarm_tone}"

	def should_ring(self):
		now = datetime.datetime.now()
		if now.hour == self.hour and now.minute == self.minute and now.second == self.second:
			return True
		else:
			return False

	def get_tone_path(self):
		return self.alarm_tones[self.alarm_tone]

	def delete(self):
		timing_objects_ls.remove(self)


class Alarm(TimingObject):
	global lifetime_objects_count
	def __init__(self, th, tm, ts, alarm_tone='basic', name=None, recurring=False):	# time in hours, minutes, seconds
		self.type = 'alarm'
		if not name or name in [to.name for to in timing_objects_ls] or name == 'q':
			if name == 'q':
				print('\nCannot name the alarm "q", defaulting to basic name.')
			self.name = 'Alarm ' + str(lifetime_objects_count + 1)
		else:
			self.name = name
		self.recurring = recurring
		self.hour = th
		self.minute = tm
		self.second = ts
		super().__init__(alarm_tone)

	def __repr__(self):
		return f"{self.name} - {self.hour}:{self.minute}:{self.second}, "\
			f"alarm_tone={self.alarm_tone}, recurring={self.recurring}"


class Timer(TimingObject):
	global lifetime_objects_count
	def __init__(self, th, tm, ts, name=None, alarm_tone='basic'):
		self.type = 'timer'
		self.recurring = False
		if not name or name in [to.name for to in timing_objects_ls] or name == 'q':
			if name == 'q':
				print('\nCannot name the timer "q", defaulting to basic name.')
			self.name = 'Timer ' + str(lifetime_objects_count + 1)
		else:
			self.name = name
		now = datetime.datetime.now()

		carry_minutes = floor((now.second + ts) / 60)
		tm += carry_minutes
		carry_hours = floor((now.minute + tm) / 60)
		th += carry_hours

		self.hour = (now.hour + th) % 24
		self.minute = (now.minute + tm) % 60
		self.second = (now.second + ts) % 60
		super().__init__(alarm_tone)


def main():
	print('\n')
	check_alarms_thread = threading.Thread(target=check_alarms, daemon=True)
	user_input_thread = threading.Thread(target=user_input, daemon=True)
	check_alarms_thread.start()
	user_input_thread.start()
	while True:
		if exit_flag:
			return

		# if not check_alarms_thread.is_alive():
		# 	check_alarms_thread = threading.Thread(target=check_alarms, daemon=True)
		# 	check_alarms_thread.start()
		if not user_input_thread.is_alive():
			user_input_thread = threading.Thread(target=user_input, daemon=True)
			user_input_thread.start()

		sleep(0.5)


def check_alarms():
	global timing_objects_ls
	alarm_ring_thread = threading.Thread()
	delete_me = None
	while True:
		for to in timing_objects_ls:
			if to.should_ring():
				if alarm_ring_thread.is_alive() and to.recurring == False:
					delete_me = to
				elif not alarm_ring_thread.is_alive():
					alarm_ring_thread = threading.Thread(target=alarm_ring, args=([to]), daemon=True)
					alarm_ring_thread.start()

		if delete_me:  # this is done so to is only removed from the list after the loop is done iterating over it
			delete_me.delete()
			delete_me = None
		sleep(check_delay)


def alarm_ring(to):
	print("\n{alarm_name}, set for {h}:{m}:{s}.".format(alarm_name=to.name,\
		h=to.hour, m=to.minute, s=to.second))
	print("Press Enter to stop.")
	# might return a weird format, but it's fine for now
	global alarm_flag
	alarm_flag = True
	p = to.get_tone_path()
	while alarm_flag:
		playsound(p)
	if to.type == 'timer':
		to.delete()
	if to.type == 'alarm':
		if not to.recurring:
			to.delete()


def user_input():
		global timing_objects_ls
		global lifetime_objects_count
		global exit_flag
		global alarm_flag
		invalid_command_flag = False
		commands_text = "\na: Create new alarm" \
				"\nt: Create new timer" \
				"\ns: See all current alarms and timers" \
				"\nd: Delete an alarm or timer" \
				"\nc: Show commands" \
				"\nq: Exit the program"
		print("What would you like to do?\n" + commands_text)
		while True:
			if invalid_command_flag:
				print("\nPlease enter a valid command.")
				invalid_command_flag = False
			ui = input("\n> ")
			if alarm_flag:
				alarm_flag = False
				continue
			if ui.lower() == "c" or ui.lower() == "h":
				print(commands_text)
			elif ui.lower() == "a":
				new_alarm()
			elif ui.lower() == 't':
				new_timer()
			elif ui.lower() == 's':
				see_objects()
			elif ui.lower() == 'd':
				delete_object()
			elif ui.lower() == 'q':
				exit_flag = True
				return
			else:
				invalid_command_flag = True


def new_alarm():
	global alarm_flag
	# global exit_flag
	# uncomment the above line to make the program terminate on q
	print("\nEnter a time for the new alarm\n(hh:mm:ss):")
	while True:
		ui = input("\n> ")
		if alarm_flag:
				alarm_flag = False
				return
		if ui.lower() == "q":
			exit_flag = True
			return
		new_time = parse_time(ui)
		if new_time:
			print("\nSelect an alarm tone?\n(if nothing is entered it will be assigned the basic tone)")
			while True:
				ui = input("\n> ")
				if alarm_flag:
					alarm_flag = False
					return
				if ui.lower() == "q":
					exit_flag = True
					return
				else:
					new_tone = ui.lower()
					new_name = input('\nGive it a name?\n(If nothing is entered it will be ' \
						f'given a the name "Alarm {lifetime_objects_count + 1}"\n\n> ')
					if alarm_flag:
						alarm_flag = False
						return
					if new_name.lower() == 'q':
						exit_flag = True
						return
					new_recurring = input("\nMake the alarm recurring?\n(y/n)\n\n> ")
					if alarm_flag:
						alarm_flag = False
						return
					if new_recurring.lower() == 'q':
						exit_flag = True
						return
					else:
						new_recurring = new_recurring.lower() == 'y'
					new_alarm = Alarm(new_time[0], new_time[1], new_time[2], alarm_tone=new_tone, \
						name=new_name, recurring=new_recurring)
					print('\nCreated new alarm: ', new_alarm)
					return
				print("\nPlease enter a valid tone or hit Enter to select basic.")


def new_timer():
	global alarm_flag
	# global exit_flag
	# uncomment the above line to make the program terminate on q
	print("\nHow long should the timer be?\n(hh:mm:ss):")
	while True:
		ui = input("\n> ")
		if alarm_flag:
				alarm_flag = False
				return
		if ui.lower() == "q":
			exit_flag = True
			return
		new_time = parse_time(ui)
		if new_time:
			print("\nSelect an alarm tone?\n(if nothing is entered it will be assigned the basic tone)")
			while True:
				ui = input("\n> ")
				if alarm_flag:
					alarm_flag = False
					return
				if ui.lower() == "q":
					exit_flag = True
					return
				else:
					new_tone = ui.lower()
					new_name = input('\nGive it a name?\n(If nothing is entered it will be ' \
						f'given a the name "Timer {lifetime_objects_count + 1}"\n\n> ')
					if alarm_flag:
						alarm_flag = False
						return
					if new_name.lower() == 'q':
						exit_flag = True
						return
					new_timer = Timer(new_time[0], new_time[1], new_time[2], alarm_tone=new_tone, \
						name=new_name)
					print('\nCreated new timer: ', new_timer)
					return
				print("\nPlease enter a valid tone or hit Enter to select basic.")


def see_objects():
	if not timing_objects_ls:
		print("\nNo alarms or timers have been set.")
	else:
		alarms = [o for o in timing_objects_ls if o.type == 'alarm']
		timers = [o for o in timing_objects_ls if o.type == 'timer']
		if alarms:
			print('\nCurrent alarms:')
			for alarm in alarms:
				print(alarm)
		if timers:
			print('\nCurrent timers:')
			for timer in timers:
				print(timer)


def delete_object():
	global alarm_flag
	global timing_objects_ls
	# global exit_flag
	# uncomment the above line to make the program terminate on q
	if not timing_objects_ls:
		print("\nThere are no alarms or timers to delete.")
		return
	print('\nEnter the name of the alarm or timer you would like to delete, or "q" to exit.')
	while True:
		delete_flag = False
		ui = input("\n> ")
		if alarm_flag:
			alarm_flag = False
			return
		if ui.lower() == 'q':
			exit_flag = True
			return
		for to in timing_objects_ls:
			if to.name == ui:
				print(f"\nDeleted {to}")
				to.delete()
				delete_flag = True
		if not delete_flag:
			print("\nThere are no alarms or timers with that name.")
		return


def parse_time(input_str):
	t_str = ''.join([d for d in input_str if d.isnumeric()])
	if len(t_str) == 6:
		th = int(t_str[:2])
		tm = int(t_str[2:4])
		ts = int(t_str[4:])
		if 0 <= th <= 23 and 0 <= tm <= 59 and 0 <= ts <= 59:
			return (th, tm, ts)
	print("Please enter a valid time.")
	return False


if __name__ == '__main__':
	main()
