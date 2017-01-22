#!/usr/bin/env python3

# The MIT License (MIT)
#
# Copyright (c) 2016 Mike Cronce <mike@quadra-tec.net>
#                    Stany MARCEL <stanypub@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""Steam Controller VDF-configurable mode"""

from steamcontroller import SteamController, SCButtons
from steamcontroller.events import EventMapper, Pos
from steamcontroller.uinput import Axes, Keys

from steamcontroller.daemon import Daemon

import gc
import json

import vdf2json

def join_duplicate_keys(ordered_pairs): # {{{
	d = {}
	for k, v in ordered_pairs:
		if k in d:
			if(type(d[k]) == list):
				d[k].append(v)
			else:
				newlist = []
				newlist.append(d[k])
				newlist.append(v)
				d[k] = newlist
		else:
			d[k] = v
	return d
# }}}

def load_vdf(path): # {{{
	f = open(path, 'r')
	obj = json.loads(vdf2json.vdf2json(f), object_pairs_hook = join_duplicate_keys)

	# Since /controller_mappings/group is a key duplicated numerous times, it
	#    makes it cumbersome to use.  This changes /controller_mappings/group
	#    to be a single-use key with a dict in it; each object in the dict is a
	#    one of these separate "group" objects, and the keys to the dict are
	#    the "id" fields of these objects.
	obj['controller_mappings']['group'] = {group['id'] : group for group in obj['controller_mappings']['group']}

	# ID -> binding doesn't really do us any good.  Flip it.
	obj['controller_mappings']['preset']['group_source_bindings'] = {value : key for key, value in obj['controller_mappings']['preset']['group_source_bindings'].items()}

	return obj
# }}}

def get_binding(group_inputs, input_name, activator): # {{{
	try:
		activator = group_inputs[input_name]['activators'][activator]
		if(type(activator) == list):
			# TODO:  Support multiples
			activator = activator[0]
		binding = activator['bindings']['binding'].split()
	except KeyError:
		return None

	# TODO:  mode_shift ... maybe more?
	if(binding[0] == 'key_press'):
		# Ugly
		binding[1] = binding[1].replace('_ARROW', '')
		binding[1] = binding[1].replace('_', '')
		binding[1] = binding[1].replace(',', '') # Items such as "key_press W, w"; everything after the comma is already trimmed by split() above, ignore trailing items for now'

		if(binding[1] == 'PERIOD'):
			binding[1] = 'DOT'

		return Keys.__getattr__('KEY_' + binding[1])
	elif(binding[0] == 'mouse_wheel'):
		# TODO:  Figure out if we actually need this; if so, add support
		return None
	elif(binding[0] == 'mouse_button'):
		return Keys.__getattr__('BTN_' + binding[1])

	return None
# }}}

def set_trackpad_config(evm, pos, group): # {{{
	button = SCButtons.RPAD if pos == Pos.RIGHT else SCButtons.LPAD
	if(group['mode'] == 'absolute_mouse'):
		evm.setPadMouse(pos)
		evm.setButtonAction(button, get_binding(group['inputs'], 'click', 'Full_Press'))
	elif(group['mode'] == 'scrollwheel'):
		# TODO:  Support configuration for scroll directions
		evm.setPadScroll(pos)
		evm.setButtonAction(button, get_binding(group['inputs'], 'click', 'Full_Press'))
	elif(group['mode'] == 'dpad'):
		inputs = group['inputs']
		# TODO:  Configurable whether or not click is required?
		evm.setPadButtons(pos, [
			get_binding(inputs, 'dpad_north', 'Full_Press'),
			get_binding(inputs, 'dpad_west', 'Full_Press'),
			get_binding(inputs, 'dpad_south', 'Full_Press'),
			get_binding(inputs, 'dpad_east', 'Full_Press')
		], clicked = True)
# }}}

def evminit(config_file_path):
	# TODO:  Dynamic gamepad definition for keys/axes based on config
	evm = EventMapper(gamepad_definition = {
		'vendor' : 0x28de,
		'product' : 0x1142,
		'version' : 0x1,
		'name' : b"Steam Controller",
		'keys' : [
			Keys.BTN_START,
			Keys.BTN_MODE,
			Keys.BTN_SELECT,
			Keys.BTN_A,
			Keys.BTN_B,
			Keys.BTN_X,
			Keys.BTN_Y,
			Keys.BTN_TL,
			Keys.BTN_TR,
			Keys.BTN_TL2,
			Keys.BTN_TR2,
			Keys.BTN_THUMBL,
			Keys.BTN_THUMBR,
			Keys.BTN_JOYSTICK
		],
		'axes' : [
			(Axes.ABS_X, -32768, 32767, 16, 128),
			(Axes.ABS_Y, -32768, 32767, 16, 128),
			(Axes.ABS_Z, 0, 255, 0, 0),
			(Axes.ABS_RZ, 0, 255, 0, 0),
			(Axes.ABS_HAT0X, -1, 1, 0, 0),
			(Axes.ABS_HAT0Y, -1, 1, 0, 0),
			(Axes.ABS_HAT1X, -1, 1, 0, 0),
			(Axes.ABS_HAT1Y, -1, 1, 0, 0)
		],
		'rels' : []
	})
	config = load_vdf(config_file_path)

	groups = config['controller_mappings']['group']
	bindings = config['controller_mappings']['preset']['group_source_bindings']

	# TODO:  Check/respect all possible "mode" entries in each group

	if('left_trackpad active' in bindings):
		group_id = bindings['left_trackpad active']
		set_trackpad_config(evm, Pos.LEFT, groups[group_id])
		print('--- Left trackpad loaded')

	if('right_trackpad active' in bindings):
		group_id = bindings['right_trackpad active']
		set_trackpad_config(evm, Pos.RIGHT, groups[group_id])
		print('--- Right trackpad loaded')

	if('joystick active' in bindings):
		group_id = bindings['joystick active']
		group = groups[group_id]
		inputs = group['inputs']
		if(group['mode'] == 'dpad'):
			evm.setStickButtons([
				get_binding(inputs, 'dpad_north', 'Full_Press'),
				get_binding(inputs, 'dpad_west', 'Full_Press'),
				get_binding(inputs, 'dpad_south', 'Full_Press'),
				get_binding(inputs, 'dpad_east', 'Full_Press')
			])
			evm.setButtonAction(SCButtons.LPAD, get_binding(inputs, 'click', 'Full_Press'))
		print('--- Joystick loaded')

	if('button_diamond active' in bindings):
		group_id = bindings['button_diamond active']
		inputs = groups[group_id]['inputs']
		evm.setButtonAction(SCButtons.A, get_binding(inputs, 'button_a', 'Full_Press'))
		evm.setButtonAction(SCButtons.B, get_binding(inputs, 'button_b', 'Full_Press'))
		evm.setButtonAction(SCButtons.X, get_binding(inputs, 'button_x', 'Full_Press'))
		evm.setButtonAction(SCButtons.Y, get_binding(inputs, 'button_y', 'Full_Press'))
		print('--- Button diamond loaded')

	if('switch active' in bindings):
		group_id = bindings['switch active']
		group = groups[group_id]
		if(group['mode'] == 'switches'):
			inputs = group['inputs']
			evm.setButtonAction(SCButtons.LB, get_binding(inputs, 'left_bumper', 'Full_Press'))
			evm.setButtonAction(SCButtons.RB, get_binding(inputs, 'right_bumper', 'Full_Press'))
			evm.setButtonAction(SCButtons.START, get_binding(inputs, 'button_escape', 'Full_Press'))
			evm.setButtonAction(SCButtons.BACK, get_binding(inputs, 'button_menu', 'Full_Press'))
			evm.setButtonAction(SCButtons.LGRIP, get_binding(inputs, 'button_back_left', 'Full_Press'))
			evm.setButtonAction(SCButtons.RGRIP, get_binding(inputs, 'button_back_right', 'Full_Press'))
		print('--- Switches loaded')

	if('left_trigger active' in bindings):
		group_id = bindings['left_trigger active']
		group = groups[group_id]
		if(group['mode'] == 'trigger'):
			evm.setTrigButton(Pos.LEFT, get_binding(group['inputs'], 'click', 'Full_Press'))
		print('--- Left trigger loaded')

	if('right_trigger active' in bindings):
		group_id = bindings['right_trigger active']
		group = groups[group_id]
		if(group['mode'] == 'trigger'):
			evm.setTrigButton(Pos.RIGHT, get_binding(group['inputs'], 'click', 'Full_Press'))
		print('--- Right trigger loaded')

	# This cannot be configured from the Steam UI.  Should we extend that file
	#    to support configuring it?
	evm.setButtonAction(SCButtons.STEAM, Keys.KEY_HOMEPAGE)

	return evm

class SCDaemon(Daemon):
	def __init__(self, pidfile, config_file):
		self.pidfile = pidfile
		self.config_file = config_file

	def run(self):
		evm = evminit(self.config_file)
		sc = SteamController(callback=evm.process)
		sc.run()
		del sc
		del evm
		gc.collect()

if __name__ == '__main__':
	import argparse

	def _main():
		parser = argparse.ArgumentParser(description = __doc__)
		parser.add_argument('command', type = str, choices = ['start', 'stop', 'restart', 'debug'])
		parser.add_argument('-c', '--config-file', type = str, required = True)
		parser.add_argument('-i', '--index', type = int, choices = [0,1,2,3], default = None)
		args = parser.parse_args()

		if args.index != None:
			daemon = SCDaemon('/tmp/steamcontroller{:d}.pid'.format(args.index), args.config_file)
		else:
			daemon = SCDaemon('/tmp/steamcontroller.pid', args.config_file)

		if 'start' == args.command:
			daemon.start()
		elif 'stop' == args.command:
			daemon.stop()
		elif 'restart' == args.command:
			daemon.restart()
		elif 'debug' == args.command:
			try:
				evm = evminit(args.config_file)
				sc = SteamController(callback=evm.process)
				sc.run()
			except KeyboardInterrupt:
				return

	_main()
