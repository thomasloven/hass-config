import base

class HelloWorld(base.Entities, base.Timers):

    def initialize(self):
        super().initialize()

        self.log("Hello from AppDaemon")
        self.log("You are now ready to run Apps!")

        self.run_in('test1', self.after_time, 3)
        self.run_in('test2', self.after_time2, 5)
        self.run_in(self.after_time2, 7)
        self.cancel_timer('test2')

        self.register_entity('taklampa', 'light.kontoret')

    def after_time(self, kwargs):
        self.log("Running function")
        self.e['taklampa']['state'] = "off"
        self.log(f"State is {self.e['taklampa']['state']}")
    def after_time2(self, kwargs):
        self.log("Running function2")
        self.e['taklampa']['state'] = "on"
        self.log(f"State is {self.e['taklampa']['state']}")
