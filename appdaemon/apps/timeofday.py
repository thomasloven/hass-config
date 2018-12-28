from datetime import timedelta

from timers import Timers
from entities import Entities
class TimeOfDay(Timers, Entities):

    TOD = ['morning', 'day', 'evening', 'night']

    def initialize(self):
        super().initialize()

        self.run_in(self.setup_inputs, 1)

    def setup_inputs(self, kwargs):
        inputs = [
                'morning',
                'day',
                'evening',
                'night',
                'sunrise',
                'sunset',
                'tod',
                'dark',
                ]
        for i in inputs:
            e = dict(self.args[i])
            name = e['name']
            default = e['default']
            del e['name']
            del e['default']
            self.register_entity(i, name, True, default, e)
            self.e[i].listen(self.update, {'trigger': 'setting', 'entity': i})

        self.update(None, None, {'trigger': 'init'})

    def update(self, old, new, kwarg):

        trigger = kwarg.get('trigger', None)

        if kwarg.get('entity', None) in ['tod', 'dark']:
            return

        self.log(f"TOD - updated by {trigger}")

        # Set up triggers for each TOD
        for t in self.TOD:
            if not trigger == t:
                self.run_once(
                        t,
                        self.update,
                        self.parse_time(self.e[t].state),
                        trigger=t
                        )

        # Set up triggers for sunrise and sunset
        if trigger != 'sunrise':
            sunrise = float(self.e['sunrise'].state)
            sunrise = timedelta(minutes=sunrise)
            sunrise = (self.sunrise() + sunrise).time()
            self.run_once(
                    'sunrise',
                    self.update,
                    sunrise,
                    trigger='sunrise'
                    )
        if trigger != 'sunset':
            sunset = float(self.e['sunset'].state)
            sunset = timedelta(minutes=sunset)
            sunset = (self.sunset() + sunset).time()
            self.run_once(
                    'sunset',
                    self.update,
                    sunset,
                    trigger='sunset'
                    )

        # Determine current time of day
        if trigger in self.TOD:
            tod = trigger
        else:
            tod = 'night'
            for t in self.TOD:
                if self.time() >= self.parse_time(self.e[t].state):
                    tod = t

        # Determine if sun is down
        if trigger == 'sunrise':
            dark = False
        elif trigger == 'sunset':
            dark = True
        elif sunrise <= self.time() <= sunset:
            dark = False
        else:
            dark = True


        self.log(f"TOD - Time of day is {tod}, sun {'has set' if dark else 'is up'}")

        # Update outputs
        self.e['dark'].state = dark
        self.e['dark'].push()
        self.e['tod'].state = tod
        self.e['tod'].push()
