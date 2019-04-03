from base import Base
import collections
import requests
import datetime

class Logger(Base):
    def initialize(self):
        super().initialize()

        self.q = collections.deque()
        self.listen_event(self.log_event, 'LOG_WRITE')

        self.listen_event(self.event)
        self.listen_state(self.state)

        self.log_write("Appdaemon logger started")

    def send(self, kwargs):
        # Send messages from the queue, but keep track of the rate limit
        while len(self.q):
            msg = self.q.popleft()
            url = self.args['channels'][msg['channel']]
            if url:
                res = requests.post(url, json={
                    "content": msg['message'],
                    "username": "Appdaemon",
                    })
            if res.status_code == 429 or res.headers['X-RateLimit-Remaining'] == 0:
                # If rate limit exceeded or nearly so
                if res.status_code == 429:
                    self.q.appendleft(msg)
                next_try = datetime.datetime.fromtimestamp(int(res.headers['X-RateLimit-Reset']))
                self.run_at(self.send, next_try)
                break

    def log_write(self, message, channel = 'log'):
        if not message:
            return
        self.q.append({
            'message': message,
            'channel': channel,
            })
        if len(self.q) == 1:
            self.run_in(self.send, 1)
    def log_event(self, ev, data, kwargs):
        self.log_write(data['message'], data['channel'])


    def event(self, name, data, kwargs):
        if name == 'call_service' and data['service'] == 'discord_log':
            return
        self.log_write("EVENT: {} {}".format(name, data))

    def state(self, entity, attribute, old, new, kwargs):
        tracked_domains = ['light', 'switch', 'device_tracker', 'binary_sensor']
        domain = entity.split('.')[0]
        if domain in tracked_domains:
            self.log_write("STATE: {} {} {} =>{}".format(entity, attribute, old, new))
