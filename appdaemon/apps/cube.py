from entities import Entities


class Cube(Entities):

    def initialize(self):
        super().initialize()

        self.lights = ['light.taklampa_kontoret', 'switch.varme_mhr', 'switch.varme_mhr_2']
        self.register_entity('upside', 'sensor.cube_up', True, 0, {})
        self.register_entity('angle', 'sensor.cube_rotaton', True, 0, {})

        self.listen_event(self.event, 'deconz_event')



    def event(self, ev, data, kwargs):
        self.log(ev)
        self.log(data)
        if data.get('id', None) == 'mi_magic_cube':
            side = data.get('event', 0) // 1000
            action = data.get('event', 0) % 10
            if side < 7 and action == 0: # Push
                self.log("Push")
                color = ['red', 'blue', 'green', 'yellow', 'purple', 'white']
                self.call_service("light/turn_on", entity_id = self.lights[0], color_name = color[side-1])
            elif side == 7 and action == 7: # Shake
                self.log("Shake")
                pass
            elif side == 7 and action == 8: # Drop
                self.log("Drop")
                pass
            elif action == side: # Double tap
                self.log("Double tap")
                if side == 1:
                    self.toggle(side)
            if 0 < side < 7:
                self.e['upside'].state = side
                self.e['upside'].push()
        if data.get('id', None) == 'switch_55':
            angle = data.get('event', 0) / 100

            oldangle = float(self.e['angle'].state)
            newangle = oldangle + angle
            newangle = newangle if newangle < 360 else 360
            newangle = newangle if newangle > 0 else 0
            self.e['angle'].state = f"{newangle:.2f}"
            self.e['angle'].push()

            self.call_service("light/turn_on", entity_id = self.lights[0], brightness_pct = newangle/3.6)


    def toggle(self, light):
        self.log("Toggling light")
        self.call_service("homeassistant/toggle", entity_id = self.lights[light-1])


