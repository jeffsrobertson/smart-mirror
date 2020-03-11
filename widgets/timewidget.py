from kivy.properties import StringProperty,BooleanProperty,NumericProperty,OptionProperty,ObjectProperty
from kivy.logger import Logger
from kivy.app import App
from datetime import datetime
from timezonefinder import TimezoneFinder
from pytz import timezone

# Custom imports
from widgets.basewidget import ScatterBase


class TimeWidget(ScatterBase):

    # Properties that are changed in settings
    type = StringProperty('Time')
    name = StringProperty('Time')
    autotime = BooleanProperty(False)
    city_id = NumericProperty(5128638)
    date_format = NumericProperty(1)
    enable_military = BooleanProperty(False)
    enable_seconds = BooleanProperty(True)
    enable_location = BooleanProperty(False)

    # Kivy properties that are not to be touched
    second = StringProperty('0')
    minute = StringProperty('0')
    hour = StringProperty('0')
    day = StringProperty('0')
    month = StringProperty('0')
    year = StringProperty('0')
    location = StringProperty('Earth')
    day_of_week = StringProperty('0')
    timezone = ObjectProperty()
    update_interval = NumericProperty(1)

    #Blocks
    seconds_block = ObjectProperty()
    date_block = ObjectProperty()
    location_block = ObjectProperty()

    def initialize(self,*args):
        app = App.get_running_app()
        Logger.info('Initializing widget {}'.format(self.name))

        #1. Remove blocks based on user settings
        if not self.enable_seconds:
            self.remove_widget(self.seconds_block)
        if self.date_format == 0:
            self.remove_widget(self.date_block)
        if not self.enable_location:
            self.remove_widget(self.location_block)

        # 2. get location from city_id
        current_city = list(filter(lambda city: city['id'] == self.city_id, app.city_list))[0]
        self.location = current_city['name']+', '+current_city['country']

        #3. get local time from coords
        lat = current_city['coord']['lat']
        lon = current_city['coord']['lon']
        timezone_str = TimezoneFinder().timezone_at(lat=lat,lng=lon)
        if timezone_str is None:
            Logger.critical('No valid timezone found for widget!')
            timezone_str = 'America/Los_Angeles'
        self.timezone = timezone(timezone_str)

        # 3. Immediately update to current time
        self.update()

    def get_date(self,id):
        id = int(id)

        utc_time = datetime.utcnow()
        current = utc_time + self.timezone.utcoffset(datetime.utcnow())
        self.date_num = current.strftime('%x')
        self.year = current.strftime("%Y")
        self.month = current.strftime("%B")
        self.month_abbr = current.strftime('%b')
        self.weekday = current.strftime("%A")
        self.weekday_abbr = current.strftime('%a')
        self.day = current.strftime("%d")

        if id==0: return 'None'
        if id==1: return '{}, {} {}, {}'.format(self.weekday,self.month,self.day,self.year)
        if id==2: return '{} {}'.format(self.month,self.day)
        if id==3: return '{} {}'.format(self.month_abbr,self.day)
        if id==4: return '{} {}, {}'.format(self.month,self.day,self.year)
        if id==5: return '{}, {} {}'.format(self.weekday,self.month,self.day)
        if id==6: return '{}, {} {}'.format(self.weekday_abbr,self.month,self.day)
        if id==7: return '{}, {} {}'.format(self.weekday_abbr,self.month_abbr,self.day)
        if id==8: return '{}'.format(self.weekday)
        if id==9: return '{}'.format(self.date_num)

        return False

    def update_time(self,*args):
        utc_time = datetime.utcnow()
        current = utc_time + self.timezone.utcoffset(datetime.utcnow())

        self.hour = current.strftime("%H") if self.enable_military else current.strftime("%I")
        self.second = current.strftime('%S')
        self.minute = current.strftime('%M')

    def update(self,*args):
        Logger.info('Updating widget {}'.format(self.name))

        #1. Get date info
        if self.date_format != 0:
            self.date_block.text = self.get_date(self.date_format)

        #2. Get time
        self.update_time()
