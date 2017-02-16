#!/usr/bin/env python

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

from steamcontroller import SteamController
from steamcontroller.config import Configurator
from steamcontroller.daemon import Daemon
from steamcontroller.events import StickModes, PadModes, TrigModes
from steamcontroller.uinput import Axes, Keys

import gc
config_dict = {
	'switch' : {
		'active' : {
			'buttons' : {
				'back' : Keys.KEY_Z,
				'start' : Keys.KEY_DOT,
				'left_bumper' : Keys.KEY_Q,
				'right_bumper' : Keys.KEY_O,
				'left_grip' : [
					'left_trigger',
					'left_trackpad',
					'joystick',
					'switch'
				],
				'right_grip' : [
					'right_trigger',
					'right_trackpad',
					'button_diamond',
					'switch'
				]
			}
		},
		'modeshift' : {
			'buttons' : {
				'back' : Keys.KEY_F1,
				'start' : Keys.KEY_F2,
				'left_bumper' : Keys.KEY_F3,
				'right_bumper' : Keys.KEY_F4,
				'left_grip' : [
					'left_trigger',
					'left_trackpad',
					'joystick',
					'switch'
				],
				'right_grip' : [
					'right_trigger',
					'right_trackpad',
					'button_diamond',
					'switch'
				]
			}
		}
	},
	'left_trigger' : {
		'active' : {
			'mode' : TrigModes.BUTTON,
			'buttons' : {'click' : Keys.KEY_1}
		},
		'modeshift' : {
			'mode' : TrigModes.BUTTON,
			'buttons' : {'click' : Keys.KEY_F5}
		}
	},
	'right_trigger' : {
		'active' : {
			'mode' : TrigModes.BUTTON,
			'buttons' : {'click' : Keys.KEY_0}
		},
		'modeshift' : {
			'mode' : TrigModes.BUTTON,
			'buttons' : {'click' : Keys.KEY_F6}
		}
	},
	'left_trackpad' : {
		'active' : {
			'mode' : PadModes.BUTTONCLICK,
			'buttons' : {
				'north' : Keys.KEY_W,
				'west' : Keys.KEY_A,
				'south' : Keys.KEY_S,
				'east' : Keys.KEY_D
			}
		},
		'modeshift' : {
			'mode' : PadModes.BUTTONCLICK,
			'buttons' : {
				'north' : Keys.KEY_F7,
				'west' : Keys.KEY_F8,
				'south' : Keys.KEY_F9,
				'east' : Keys.KEY_F10
			}
		}
	},
	'right_trackpad' : {
		'active' : {
			'mode' : PadModes.BUTTONTOUCH,
			'buttons' : {
				'click' : Keys.KEY_KP5,
				'north' : Keys.KEY_KP8,
				'west' : Keys.KEY_KP4,
				'south' : Keys.KEY_KP2,
				'east' : Keys.KEY_KP6
			}
		},
		'modeshift' : {
			'mode' : PadModes.BUTTONCLICK,
			'buttons' : {
				'north' : Keys.KEY_KP7,
				'west' : Keys.KEY_KP3,
				'south' : Keys.KEY_KP1,
				'east' : Keys.KEY_KP9
			}
		}
	},
	'joystick' : {
		'active' : {
			'mode' : StickModes.BUTTON,
			'buttons' : {
				'click' : Keys.KEY_GRAVE,
				'north' : Keys.KEY_UP,
				'west' : Keys.KEY_DOWN,
				'south' : Keys.KEY_LEFT,
				'east' : Keys.KEY_RIGHT
			},
		},
		'modeshift' : {
			'mode' : StickModes.BUTTON,
			'buttons' : {
				'click' : Keys.KEY_T,
				# Vim-style "HJKL" but on "4567"
				'north' : Keys.KEY_6,
				'west' : Keys.KEY_4,
				'south' : Keys.KEY_5,
				'east' : Keys.KEY_7
			},
		}
	},
	'button_diamond' : {
		'active' : {
			'buttons' : {
				'a' : Keys.KEY_K,
				'b' : Keys.KEY_J,
				'x' : Keys.KEY_L,
				'y' : Keys.KEY_SEMICOLON
			}
		},
		'modeshift' : {
			'buttons' : {
				'a' : Keys.KEY_END,
				'b' : Keys.KEY_HOME,
				'x' : Keys.KEY_DELETE,
				'y' : Keys.KEY_INSERT
			}
		}
	}
}

class SCDaemon(Daemon):
	def __init__(self, pidfile):
		self.pidfile = pidfile
		self.logfile = '/var/log/steam-controller.log'

	def run(self):
		config = Configurator('Steam Controller with Axes')
		config.import_config(config_dict)
		sc = SteamController(callback = config.evm.process)
		sc.run()
		del sc
		del config
		gc.collect()

if __name__ == '__main__':
	import argparse

	def _main():
		parser = argparse.ArgumentParser(description = __doc__)
		parser.add_argument('command', type = str, choices = ['start', 'stop', 'restart', 'debug'])
		parser.add_argument('-i', '--index', type = int, choices = [0,1,2,3], default = None)
		args = parser.parse_args()

		if args.index != None:
			daemon = SCDaemon('/tmp/steamcontroller{:d}.pid'.format(args.index))
		else:
			daemon = SCDaemon('/tmp/steamcontroller.pid')

		if 'start' == args.command:
			daemon.start()
		elif 'stop' == args.command:
			daemon.stop()
		elif 'restart' == args.command:
			daemon.restart()
		elif 'debug' == args.command:
			try:
				config = Configurator('Steam Controller with Axes')
				config.import_config(config_dict)
				sc = SteamController(callback = config.evm.process)
				sc.run()
			except KeyboardInterrupt:
				return

	_main()
