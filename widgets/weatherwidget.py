from kivy.properties import StringProperty,BooleanProperty,NumericProperty,ObjectProperty
from widgets.basewidget import ScatterBase
from kivy.uix.floatlayout import FloatLayout
from kivy.app import App
from kivy.logger import Logger
from kivy.network.urlrequest import UrlRequest
from kivy.clock import Clock

import time
from datetime import datetime


class WeatherWidget(ScatterBase):

    # User settings
    type = StringProperty('Weather')
    name = StringProperty('Weather')
    autolocation = BooleanProperty(False)
    metric_units = BooleanProperty(True)  # True = metric, False = freedom
    display_units = BooleanProperty(False)
    display_location = BooleanProperty(True)
    display_forecast = BooleanProperty(True)
    forecast_days = NumericProperty(1)
    city_id = NumericProperty(5128638)
    city_name = StringProperty('New York')

    # Kivy properties, no touchy
    temperature = StringProperty('0.0°')
    description = StringProperty('Sunny')
    current_weather_icon = StringProperty('images/weather/day_clearsky.png')
    update_interval = NumericProperty(300) #[s]

    temperature_block = ObjectProperty()
    icon_block = ObjectProperty()
    description_block = ObjectProperty()
    location_block = ObjectProperty()
    forecast_block = ObjectProperty()
    forecast_header = ObjectProperty()

    def initialize(self):

        # 1. Add/remove blocks based on user settings
        if not self.display_location:
            self.location_block.font_size = 0
        if not self.display_forecast:
            self.remove_widget(self.forecast_block)

        # 2. Custom settings
        if self.display_units:
            self.temperature += 'C' if self.metric_units else 'F'

        # 3. Update immediately to fetch temp, etc
        Clock.schedule_once(self.update, 0)

    # First half of update, requests weather data from server
    def update(self, *args):
        app = App.get_running_app()

        # 1. Get current weather (temperature, weather icon, location, and description)
        Logger.info('Getting weather data...')
        api_key = app.sys['weather_api_key']
        print('Getting weather for city id {}'.format(self.city_id)) #jeff
        search_url = 'http://api.openweathermap.org/data/2.5/weather?id={}&appid={}'.format(self.city_id, api_key)
        request = UrlRequest(search_url, self.get_weather)

        # 2. Build forecast table
        if self.display_forecast:

            # 2a. Clear forecast table, redraw header
            self.forecast_block.clear_widgets()
            self.forecast_block.add_widget(self.forecast_header)

            # 2b. Get forecast data
            Logger.info('Fetching forecast data...')
            api_key = app.sys['weather_api_key']
            print('Getting forecast for city id {}'.format(self.city_id))
            search_url = 'http://api.openweathermap.org/data/2.5/forecast?id={}&appid={}'.format(self.city_id, api_key)
            request = UrlRequest(search_url, self.get_forecast)

    # Fetch current weather (only does this on the pi)
    def get_weather(self, request, data):
        Logger.info('Received weather data!')

        # 1. Set temperature
        temp_kelvin = data['main']['temp']
        temperature = self.get_temperature(temp_kelvin)
        self.temperature = str(round(temperature, 1))+'°'

        # 2. Set temperature units
        if self.display_units:
            self.temperature += 'C' if self.metric_units else 'F'

        #3. Set weather image
        icon_id = data['weather'][0]['id']
        sunrise = data['sys']['sunrise']
        sunset = data['sys']['sunset']
        current_time = time.time()
        period = 'day' if (current_time>sunrise and current_time<sunset) else 'night'
        self.current_weather_icon = self.get_weather_icon(icon_id,period)

        #4. Set weather description
        self.description = data['weather'][0]['description']

    # Fetch forecast (only does this on pi)
    def get_forecast(self, request, data):

        days = ['Mon.', 'Tues.', 'Wed.', 'Thurs.', 'Fri.', 'Sat.', 'Sun.']
        current_weekday_id =  datetime.now().weekday()
        weekday_ids = [datetime.fromtimestamp(data['list'][i]['dt']).weekday() for i in range(data['cnt'])]

        # 1. Go through days, one at a time, and group data into lists
        for d in range(int(self.forecast_days)):
            desired_weekday_id = (current_weekday_id+d+1) % 7
            list_of_highs = []
            list_of_lows = []
            list_of_conditions = []
            for i in range(data['cnt']):
                if weekday_ids[i]==desired_weekday_id:
                    list_of_highs.append(self.get_temperature(data['list'][i]['main']['temp_max']))
                    list_of_lows.append(self.get_temperature(data['list'][i]['main']['temp_min']))
                    list_of_conditions.append(data['list'][i]['weather'][0]['main'])

            # Low/High temp is absolute lowest/highest of that day
            low_temp = min(list_of_lows)
            high_temp = max(list_of_highs)

            # Determine weather condition
            conditions, conditions_image = self.get_forecast_conditions(list_of_conditions)

            # Add this day's forecast to table
            new_forecast_row = ForecastRow(day=days[desired_weekday_id],
                                           conditions_image=conditions_image,
                                           conditions=conditions,
                                           high_temp=str(round(high_temp, 0)),
                                           low_temp=str(round(low_temp, 0)))
            new_forecast_row.height = .15*self.temperature_block.font_size
            self.forecast_block.add_widget(new_forecast_row)

    # Convert temperature (in K) to preferred units
    def get_temperature(self,temp,*args):
        if self.metric_units:
            return (temp-273.15)*(9/5)+32
        else:
            return temp - 273.15

    def get_weather_icon(self,id,time):

        # Day or night
        image_path = 'images/weather/'+time+'_'

        if id==800:
            image_path += 'clearsky'
        elif id in [801,802]:
            image_path += 'fewclouds'
        elif id in [803,804]:
            image_path += 'overcast'
        elif id in [500]:
            image_path += 'lightrain' #clouds with sun and drizzle
        elif id in [300,301,302,310,311,312,313,314,321]:
            image_path += 'overcastlightrain' #drizzle with clouds
        elif id in [501,502,503]:
            image_path += 'overcastrain' #clouds with solid rain
        #TODO: thunderstorms
        #TODO: Snow
        else:
            image_path += 'invalid'

        image_path += '.png'

        return image_path

    def get_forecast_conditions(self, list_of_conditions):
        '''
        Possible conditions (from openweathermap):
            Thunderstorm
            Drizzle
            Rain
            Snow
            Clear
            Clouds
        '''

        '''
        Custom Conditions:         IDs:
        Clear sky                   800
        Few clouds                  801, 802, 803
        Cloudy (or overcast?)       804
        Light rain                  500,501
        Rain                        502,503,504,511,520
        Heavy rain
        Light snow
        Snow
        Heavy snow
        Rain & Snow
        '''

        img = 'images/weather/day_{}.png'

        if 'Snow' in list_of_conditions:
            return 'Snow!',img.format('invalid')
        if 'Thunderstorm' in list_of_conditions:
            return 'Thunderstorm!',img.format('invalid')
        if 'Rain' in list_of_conditions:
            return 'Rain',img.format('overcastrain')
        if 'Drizzle' in list_of_conditions:
            return 'Drizzle',img.format('lightrain')
        if 'Clouds' in list_of_conditions:
            return 'Cloudy',img.format('fewclouds')
        if 'Clear' in list_of_conditions:
            return 'Clear skies',img.format('clearsky')
        return 'Unknown',img.format('invalid')


class ForecastRow(FloatLayout):
    day = StringProperty()
    conditions_image = StringProperty('images/clear_background.png')
    conditions = StringProperty()
    high_temp = StringProperty()
    low_temp = StringProperty()


'''
READING FORECAST DATA:
data = {
'cod': 200
'message': .0094
'cnt': 40               
'list':[{'dt':
         'main': 1546128000,
         'weather':[{
                     'id': 800
                     'main': 'Clear' - 
                     'description': 'clear sky' -- OPTIONS: 'clear sky', 'scattered clouds', 'few clouds', 'broken clouds', 'light rain' ...
                     'icon': '01n' }]
         'clouds':
         'wind':
         'rain':
         'snow':
         'sys':
         'dt_txt':
         }
         ... 
        (repeats 40 times)
        ]

'city':{
        'id':
        'name':
        'coord':
        'country':
        }
}

'''












