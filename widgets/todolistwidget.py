from kivy.uix.relativelayout import RelativeLayout
from kivy.properties import StringProperty,ListProperty,ObjectProperty,BooleanProperty,NumericProperty

# Custom imports
from widgets.basewidget import ScatterBase

class ToDoListWidget(ScatterBase):

    # Settings
    title = StringProperty('To Do List!!!!!!!!!!!:')
    to_do_list = ListProperty(['this', 'is', 'a', 'list'])
    to_do_list_checks = ListProperty([True, True, False, False])
    update_interval = NumericProperty(300)

    to_do_layout = ObjectProperty()

    def initialize(self,*args):

        #1. Build list
        for l in range(len(self.to_do_list)):
            new_list_item = ToDoListItem(text=self.to_do_list[l], checked=self.to_do_list_checks[l])
            self.to_do_layout.add_widget(new_list_item)
            print('Added item {}, min height = {}'.format(l,self.to_do_layout.minimum_height))

    def update(self,*args):
        pass

class ToDoListItem(RelativeLayout):
    text = StringProperty()
    checked = BooleanProperty()
