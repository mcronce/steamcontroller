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
				'back' : Keys.BTN_SELECT,
				'start' : Keys.BTN_START,
				'left_bumper' : Keys.BTN_LEFT,
				'right_bumper' : Keys.BTN_RIGHT,
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
				'back' : Keys.BTN_BACK,
				'start' : Keys.BTN_FORWARD,
				'left_bumper' : Keys.BTN_TOP,
				'right_bumper' : Keys.BTN_TOP2
			}
		}
	},
	'left_trigger' : {
		'active' : {
			'mode' : TrigModes.BUTTON,
			'buttons' : {'click' : Keys.BTN_TL}
		},
		'mdoeshift' : {
			'mode' : TrigModes.BUTTON,
			'buttons' : {'click' : Keys.BTN_TL2}
		}
	},
	'right_trigger' : {
		'active' : {
			'mode' : TrigModes.BUTTON,
			'buttons' : {'click' : Keys.BTN_TR}
		},
		'mdoeshift' : {
			'mode' : TrigModes.BUTTON,
			'buttons' : {'click' : Keys.BTN_TR2}
		}
	},
	'left_trackpad' : {
		'active' : {
			'mode' : PadModes.AXIS,
			'buttons' : {'click' : Keys.BTN_THUMBL},
			'axes' : [
				(Axes.ABS_HAT0X, -32768, 32767, 16, 128),
				(Axes.ABS_HAT0Y, -32768, 32767, 16, 128)
			]
		},
		'modeshift' : {
			'mode' : PadModes.AXIS,
			'buttons' : {'click' : Keys.BTN_GEAR_DOWN},
			'axes' : [
				(Axes.ABS_HAT2X, -32768, 32767, 16, 128),
				(Axes.ABS_HAT2Y, -32768, 32767, 16, 128)
			]
		}
	},
	'right_trackpad' : {
		'active' : {
			'mode' : PadModes.AXIS,
			'buttons' : {'click' : Keys.BTN_THUMBR},
			'axes' : [
				(Axes.ABS_HAT1X, -32768, 32767, 16, 128),
				(Axes.ABS_HAT1Y, -32768, 32767, 16, 128)
			]
		},
		'modeshift' : {
			'mode' : PadModes.AXIS,
			'buttons' : {'click' : Keys.BTN_GEAR_UP},
			'axes' : [
				(Axes.ABS_HAT3X, -32768, 32767, 16, 128),
				(Axes.ABS_HAT3Y, -32768, 32767, 16, 128)
			]
		}
	},
	'joystick' : {
		'active' : {
			'mode' : StickModes.AXIS,
			'buttons' : {'click' : Keys.BTN_C},
			'axes' : [
				(Axes.ABS_X, -32768, -32767, 16, 128),
				(Axes.ABS_Y, -32768, -32767, 16, 128),
			]
		},
		'modeshift' : {
			'mode' : StickModes.AXIS,
			'buttons' : {'click' : Keys.BTN_Z},
			'axes' : [
				(Axes.ABS_RX, -32768, -32767, 16, 128),
				(Axes.ABS_RY, -32768, -32767, 16, 128),
			]
		}
	},
	'button_diamond' : {
		'active' : {
			'buttons' : {
				'a' : Keys.BTN_A,
				'b' : Keys.BTN_B,
				'x' : Keys.BTN_X,
				'y' : Keys.BTN_Y
			}
		},
		'modeshift' : {
			'buttons' : {
				'a' : Keys.BTN_TRIGGER_HAPPY,
				'b' : Keys.BTN_TRIGGER_HAPPY1,
				'x' : Keys.BTN_TRIGGER_HAPPY2,
				'y' : Keys.BTN_TRIGGER_HAPPY3
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
