from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.lang import Builder
from kivy.storage.dictstore import DictStore
from kivy.core.text import LabelBase
from kivy.properties import StringProperty, NumericProperty,BooleanProperty
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.core.window import Window

import socket
import pickle
import threading
import struct
from copy import deepcopy
from functools import partial
import time
import json


# Custom mirror widgets
from widgets import *

LabelBase.register(name="RobotoCondensed",
                    fn_regular="fonts/RobotoCondensed-Regular.ttf",
                    fn_bold="fonts/RobotoCondensed-Bold.ttf",
                    fn_italic="fonts/RobotoCondensed-LightItalic.ttf",
                    fn_bolditalic="fonts/RobotoCondensed-BoldItalic.ttf")

MIRROR_ID = 'xxx' #UNIQUE factory id for mirror. No two mirrors will have same id
MIRROR_WEATHER_API_KEY = '02f530dcf5918f582ac314f501fbcdcc' #Key should be unique to each mirror
MIRROR_RATIO = 1.33#.5625

FRESH_SYS = {'last_edited':0.0,'ratio':MIRROR_RATIO,'active_config':None,
             'mirror_id':MIRROR_ID,'mirror_name':'New Mirror','weather_api_key':MIRROR_WEATHER_API_KEY}
FRESH_CONFIG_FILE = {'sys':deepcopy(FRESH_SYS),'configs':{}}

WIDGET_FONT = 'RobotoCondensed'

Builder.load_string('''
<NoConfigWarning>:
    text: 'You have not created a configuration for your mirror!'
    size_hint: (None,None)
    font_size: 50
    size: self.texture_size
    pos_hint: {'center_x':.5,'center_y':.5}

''')
Builder.load_file('widgets/kv/weather.kv')
Builder.load_file('widgets/kv/time.kv')
Builder.load_file('widgets/kv/clock.kv')


class RootLayout(FloatLayout):

    def __init__(self, **kwargs):
        super(RootLayout, self).__init__(**kwargs)
        Clock.schedule_once(self.load_mirror, 0)

    def load_mirror(self, *args):
        app = App.get_running_app()

        # 1. Clear mirror
        self.unschedule_widget_updates()
        self.clear_widgets()

        # 2. If no active config found (aka new mirror), issue warning
        active_config = app.sys['active_config']
        if active_config is None:
            Logger.info('No active config found in pickle. Issuing warning')
            self.add_widget(NoConfigWarning())
            return

        # 3. Load in mirror settings
        self.load_mirror_settings(active_config)

        # 4. Generate widgets one at a time
        widget_settings = app.configs[active_config]['widget_settings']
        for widget_name, widget_config in widget_settings.items():

            # 4a. Generate instance of widget
            new_widget = app.generate_widget(widget_config['type'], config=widget_config)
            new_widget.name = widget_name

            # 4b. Configure size, scale, rotation
            new_widget.parent_width = self.width
            new_widget.parent_height = self.height
            new_widget.scale = widget_config['magnitude']
            new_widget.rotation = widget_config['tilt']

            # 4c. Assign position
            x = self.width*widget_config['position'][0]
            y = self.height*widget_config['position'][1]
            new_widget.pos = (x, y)
            Logger.info("Adding widget '{}' to mirror.".format(widget_name))

            # 4d. Schedule widget updates
            Clock.schedule_interval(new_widget.update, new_widget.update_interval)

            # 4e. Add to mirror
            self.add_widget(new_widget)

            # 4f. Check widget to make sure it is still in bounds of mirror
            Clock.schedule_once(new_widget.check_widget, 0)

    # TODO
    def load_mirror_settings(self, active_config, *args):
        app = App.get_running_app()

        mirror_settings = app.configs[active_config]['mirror_settings']
        print('Loading mirror settings for config {}. **Not implemented yet**'.format(active_config))
        print('The unrotated Window size is ', Window.system_size)
        print('The rotated Window size is ',Window.size)

    def unschedule_widget_updates(self, *args):
        for child in self.children:
            Clock.unschedule(child.update)


class NoConfigWarning(Label):
    def update(self, *args):
        pass

class Mirror(App):

    #configs = DictProperty()
    #sys = DictProperty()
    mirror_name = StringProperty()
    multicast_ip = StringProperty('224.3.29.71')
    multicast_port = NumericProperty(11088)
    store = DictStore('mirror_config.pckl')

    dgram_server = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    tcp_server = socket.socket()

    # Returns {'Mirror name':[(ip,port),last_edited_time]} to client
    def start_dgram_server(self):

        # 1. Create datagram socket
        self.dgram_server.bind(('',self.multicast_port))
        Logger.info('Multicast server created, on ip {}, port {}'.format(self.multicast_ip,self.multicast_port))

        # 2. Add socket to multicast group
        multicast_ip = socket.inet_aton(self.multicast_ip)  # Converts ip into packed 32-bit binary'
        mreq = struct.pack('4sL', multicast_ip, socket.INADDR_ANY)
        self.dgram_server.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        # 3. Set socket to listening mode
        while True:
            Logger.info('Awaiting dgram message on ip {}, port {}'.format(self.multicast_ip, self.multicast_port))

            # 4. Receive request from client
            data_encoded, address =  self.dgram_server.recvfrom(4096)
            Logger.info('Received {} bytes on datagram server, from ip {}'.format(len(data_encoded), address))
            try:
                data, request = pickle.loads(data_encoded)
            except:
                Logger.error('Failed to unpickle data!')

            # 5. Reply to client with name and id of mirror, and when it was last edited
            # Packaged in tuple of form: (mirror_id,mirror_name,last_edited)
            if request == 'name':
                try:
                    mirror_data = self.store.get(MIRROR_ID)
                    mirror_name = mirror_data['sys']['mirror_name']
                    last_edited = mirror_data['sys']['last_edited']
                    reply = pickle.dumps((MIRROR_ID,mirror_name,last_edited),protocol=2)
                except:
                    Logger.error('Was unable to find and/or pickle mirror data! Failed to reply to multicast.')
                try:
                    self.dgram_server.sendto(reply, address)
                    Logger.info('Replied to multicast request from {}'.format(address))
                except:
                    Logger.error('Failed to send reply to multicast!')

        Logger.info('Shutting down DGRAM server.')

    def start_tcp_server(self):

        # 1. Create socket
        try:
            self.tcp_server.bind(('',54321))
            self.tcp_server.listen(5)
            Logger.info('Created TCP server.')
        except:
            Logger.critical('Failed to create TCP server!')

        # 2. Set to listening mode
        while True:
            Logger.info('Awaiting message on TCP server.')
            client, address = self.tcp_server.accept()
            Logger.info('Received TCP connection from ip {}.'.format(address))

            # 3. Unpack data from client. format is tuple of (data,request)
            try:
                data_pickled = client.recv(4096)
                data, request = pickle.loads(data_pickled)
                Logger.info('Unpickled {} bytes via TCP connection. Request: {}'.format(len(data_pickled), request))
            except:
                Logger.error('Failed to unpack mirror data on TCP server!')
                continue

            # 4. If request is to update_phone, send mirror info back in tuple (mirror_id,mirror_data)
            # mirror_data is packaged in dict of form {'sys': ..., 'config': ...}
            if request=='update_phone':
                Logger.info('Mirror data was requested from client. Packaging config files...')
                try:
                    mirror_configs = self.store.get(MIRROR_ID)
                    configs_pickled = pickle.dumps((MIRROR_ID, mirror_configs), protocol=2)
                except:
                    Logger.error('Failed to load and/or pickle mirror configs!')
                try:
                    client.send(configs_pickled)
                    Logger.info('Send mirror info back to client. Closing socket.')
                except:
                    Logger.error('Failed to send mirror info back to client. Closing socket.')

                client.close()
                continue

            # 6. If request is to update_mirror, updates mirror's info with received data
            # Received data is of the form {'sys': ...,'configs': ...}
            if request=='update_mirror':
                Logger.info('Updating mirror with received config.')
                try:
                    self.store.put(MIRROR_ID, sys=data['sys'], configs=data['configs'])
                except:
                    Logger.error('Failed to save new mirror data to storage.')

                # Have to schedule these so they're done on the main thread
                Clock.schedule_once(self.load_mirror_info, 0)
                Clock.schedule_once(self.root.load_mirror, 0)
                continue

        Logger.info('Shutting down TCP server.')

    def generate_widget(self, widget_type, config={}):

        # 1. Create default widget
        if widget_type == 'Time':
            new_widget = TimeWidget()
        elif widget_type == 'Weather':
            new_widget = WeatherWidget()
        elif widget_type == 'Clock':
            new_widget = ClockWidget()
        else:
            Logger.critical("Not implemented yet how'd you get here")
            return False

        # 2. Load specified configuration
        config_keys = config.keys()
        new_widget_properties = new_widget.properties()  # loads ALL kivy properties in list
        for key in config_keys:
            if key in new_widget_properties:  # if key in config file is a kivy property of the widget, update it with that value
                setattr(new_widget, key, config[key])

        # 3. Initialize new widget to reflect specified config settings
        new_widget.initialize()

        return new_widget

    def on_stop(self):
        Logger.info('Application closed. Shutting down TCP and UDP servers.')
        self.tcp_server.close()
        self.dgram_server.close()

    def load_mirror_info(self, *args):

        # 1. If no config file exists, create one
        if not self.store.keys():
            Logger.info("Couldn't find anything in mirror_config.pckl. Creating new one.")
            self.store.clear()
            self.store.put(MIRROR_ID, sys=deepcopy(FRESH_CONFIG_FILE['sys']), configs=deepcopy(FRESH_CONFIG_FILE['configs']))

        # 2. Extract mirror info from storage
        config_data = self.store.get(MIRROR_ID)
        self.sys = config_data['sys']
        self.configs = config_data['configs']
        Logger.info('Loaded mirror info into memory.')

    def load_city_list(self):
        ts = time.time()
        with open('city_list.json') as f:
            self.city_list = json.load(f)
        Logger.info('Loaded city list in {} seconds.'.format(time.time()-ts))

    def build(self):

        #0. Load city list
        # Load city list into memory (takes like ~1 s, so does it asynchronously)
        self.load_city_list()

        #1. Load mirror config info
        self.load_mirror_info()

        #2. Start multicast server
        # This server's only purpose is to listen for a ping and send back its name, id, and last edited
        dgram_thread = threading.Thread(target=self.start_dgram_server)
        dgram_thread.start()

        #3. Start server to listen for TCP data
        # This server is used for updating mirror config info from phone
        tcp_thread = threading.Thread(target=self.start_tcp_server)
        tcp_thread.start()

        #4. Intialize and load mirror
        r = RootLayout()

        return r


Mirror().run()

#Bugs:
# 1. Open mirror, then open app. If app is newer, it will update mirror automatically but then mirror closes.
