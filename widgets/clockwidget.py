from kivy.properties import NumericProperty,ObjectProperty,StringProperty,BooleanProperty
from math import cos,sin,pi
from kivy.graphics import Line,InstructionGroup
from kivy.uix.label import Label
import datetime

# Custom imports
from widgets.basewidget import ScatterBase

class ClockWidget(ScatterBase):
    #Properties that are changed in settings
    type = StringProperty('Clock')
    name = StringProperty('Clock')
    update_interval = NumericProperty(1)
    enable_seconds = BooleanProperty(True)

    # Kivy properties, no touchy
    clock_layout = ObjectProperty()
    second_hand = InstructionGroup()
    minute_hand = InstructionGroup()
    hour_hand = InstructionGroup()

    def initialize(self,*args):

        #1. Draw tick marks and numbers
        for i in range(1,13):
            radians = 30*i*pi/180
            radius = .5*self.width

            # Draw ticket mark first
            tick_length = .1*radius

            start_x = radius + radius*sin(radians)
            start_y = radius + radius*cos(radians)

            end_x = radius + (radius - tick_length)*sin(radians)
            end_y = radius + (radius - tick_length)*cos(radians)

            with self.clock_layout.canvas:
                Line(points=[start_x,start_y,end_x,end_y],width=.0085*self.width)

            # Write number
            number = Label(text=str(i),
                           font_size=.1*self.width,
                           size_hint=(None,None),
                           bold=True)
            number.size = number.texture_size
            number.center_x =  radius + (radius - 2.5*tick_length)*sin(radians)
            number.center_y = radius + (radius - 2.5*tick_length)*cos(radians)

            # Add to layout
            self.clock_layout.add_widget(number)

        # 2.Initialize second, minute, and hour hands
        if self.enable_seconds:
            self.clock_layout.canvas.add(self.second_hand)
        self.clock_layout.canvas.add(self.minute_hand)
        self.clock_layout.canvas.add(self.hour_hand)

        # 2. Force update
        self.update()

    def update(self,*args):
        radius = .5*self.width

        # 1. Get time
        now = datetime.datetime.now()

        # 2. Draw second
        if self.enable_seconds:
            radians = (now.second*6)*pi/180
            start_x = start_y = radius
            end_x = radius + .9*radius*sin(radians)
            end_y = radius + .9*radius*cos(radians)
            self.clock_layout.canvas.remove(self.second_hand)
            self.second_hand = InstructionGroup()
            self.second_hand.add(Line(points=[start_x,start_y,end_x,end_y],width=.005*self.width))
            self.clock_layout.canvas.add(self.second_hand)

        # 3. Draw minute
        radians = (now.minute*6)*pi/180
        start_x = start_y = radius
        end_x = radius + .8*radius*sin(radians)
        end_y = radius + .8*radius*cos(radians)
        self.clock_layout.canvas.remove(self.minute_hand)
        self.minute_hand = InstructionGroup()
        self.minute_hand.add(Line(points=[start_x,start_y,end_x,end_y],width=.0075*self.width))
        self.clock_layout.canvas.add(self.minute_hand)

        # 4. Draw hour
        radians = (now.hour*30)*pi/180
        start_x = start_y = radius
        end_x = radius + .6*radius*sin(radians)
        end_y = radius + .6*radius*cos(radians)
        self.clock_layout.canvas.remove(self.hour_hand)
        self.hour_hand = InstructionGroup()
        self.hour_hand.add(Line(points=[start_x,start_y,end_x,end_y],width=.0125*self.width))
        self.clock_layout.canvas.add(self.hour_hand)


# To do: For clock settings have option of fluid movement or ticks (for seconds hand)
# To do: Clock setting to choose clock style - can have a few options like classic, modern, regal, etc
