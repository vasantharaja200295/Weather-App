import threading
from kivy.clock import mainthread
from kivy.properties import StringProperty
from kivymd.uix.list import OneLineListItem
import requests
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.screenmanager import ScreenManager
from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.core.window import Window
from kivymd.uix.menu import MDDropdownMenu
from datetime import date
from kivy.storage.jsonstore import JsonStore


today = date.today()

settingsKV = '''
MDScreen:
    name:"settings"
    MDFloatLayout:
        MDLabel:
            text:"Settings"
            pos_hint:{"center_x":.2, "center_y":.95}
            halign:"center"
            font_size:"30sp"
            font_name:'Gilroy-SemiBold.ttf'
            theme_text_color:'Custom'
            text_color:rgba(40, 40, 43, 255)

        MDLabel:
            text:"Default Location"
            halign:"center"
            font_size:"18sp"
            font_name:'Gilroy-Medium.ttf'
            pos_hint:{"center_x":.24, "center_y":.85}

        MDLabel:
            text:"Set Current location as default"
            halign:"center"
            font_size:"14sp"
            font_name:'Gilroy-Regular.ttf'
            pos_hint:{"center_x":.324, "center_y":.81}
            theme_text_color:"Secondary"

        MDCard:
            md_bg_color:rgba(84, 186, 227, 255)
            pos_hint:{"center_x":.83, "center_y":.81}
            on_press:app.set_default_loc()
            radius:[5,5,5,5]
            size_hint:.25,.05
            MDLabel:
                text:"set"
                halign:"center"
                font_size:"14sp"
                font_name:'Gilroy-Regular.ttf'
                theme_text_color:"Primary"
                color:1,1,1,1

        MDTextButton:
            text:"Reset Default location"
            halign:"center"
            font_size:"12sp"
            font_name:'Gilroy-Light.ttf'
            pos_hint:{"center_x":.22, "center_y":.775}
            color:rgba(247, 193, 77, 255)
            on_press:app.reset_default_loc()

        MDLabel:
            text:"Weather App V 1.2"
            halign:"center"
            font_size:"14sp"
            font_name:'Gilroy-Regular.ttf'
            pos_hint:{"center_x":.5, "center_y":.171}
            theme_text_color:"Hint"
        MDLabel:
            text:"Created by Vsantharaja CSE"
            halign:"center"
            font_size:"14sp"
            font_name:'Gilroy-Regular.ttf'
            pos_hint:{"center_x":.5, "center_y":.141}
            theme_text_color:"Hint"
'''


class IconListItem(OneLineListItem):
    icon = StringProperty()


Window.size = (350, 650)


# noinspection PyGlobalUndefined
def on_key(window, key, *args):
    if key == 27:  # the esc key
        if screen_manager.current_screen.name == "settings":
            screen_manager.transition.direction = 'left'
            screen_manager.current = 'weather'
            return True
        elif screen_manager.current_screen.name == "weather":
            return False


# noinspection PyGlobalUndefined
class WeatherApp(MDApp):
    menu = None
    default_location = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.API_KEY = "773250af1fc04010a7165318211609"
        self.previous_text = ''  # Initializing variables
        self.name_list = []
        self.text = ''
        self.response = None
        self.search_complete = False
        self.menu_open = False
        self.weather_thread = threading.Thread(target=self.search_weather)

    def set_item(self, text__item):
        if self.search_complete:
            self.root.get_screen('weather').ids.field.text = text__item
            self.root.get_screen('weather').ids.field.focused = False
            Clock.unschedule(self.text_search)
            self.menu_dismiss()
            self.root.get_screen('weather').ids.city.text = text__item
            self.weather_forecast(text__item)

    # Callback function to initiate the search

    def set_default_loc(self):
        default_loc = self.root.get_screen('weather').ids.city.text
        print("Default Location:", default_loc)
        store = JsonStore('config.json')
        store.put(key='config', default_location=default_loc)
        return

    @staticmethod
    def reset_default_loc():
        store = JsonStore('config.json')
        store.put(key='config', default_location='')
        return

    def return_default_loc(self):
        store = JsonStore('config.json')
        default_loc = store.get('config')['default_location']
        if default_loc != "":
            self.root.get_screen('weather').ids.city.text = default_loc
            return default_loc
        else:
            print("No Default Location set")
            return None

    def autocomplete(self):
        if self.root.get_screen('weather').ids.field.text != '':
            self.root.get_screen('weather').ids.field.text = ''
        Clock.schedule_interval(self.text_search, 1)
        return

    def text_search(self, *args):
        self.text = self.root.get_screen('weather').ids.field.text
        if self.text == '':
            pass
        if self.text == self.previous_text:
            pass
        else:
            self.previous_text = self.text
            search_thread = threading.Thread(target=(lambda x: self.search_term(x))(self.text))
            search_thread.start()
        self.previous_text = self.text

    def menu_dismiss(self):
        self.menu.dismiss()
        self.menu_open = False
        return

    def search_term(self, term, *args):
        try:
            self.search_complete = False

            query_type = 'search'

            BASE_URL = f"http://api.weatherapi.com/v1/{query_type}.json?key={self.API_KEY}&q={term}"

            URL = BASE_URL
            if not self.search_complete:
                if len(self.root.get_screen('weather').ids.field.text) >= 4:
                    response = requests.get(URL)
                    self.response = response.json()
                    for item in self.response:
                        self.name_list.append(item['name'])
                    self.display_search()
                    self.search_complete = True
                    return
        except Exception as e:
            print(e)

    def display_search(self):

        menu_items = [
            {
                "viewclass": "IconListItem",
                "icon": "git",
                "height": dp(48),
                "text": f"{i['name']}",
                "on_release": lambda x=f"{i['name']}": self.set_item(x),
            } for i in self.response]

        self.menu = MDDropdownMenu(
            caller=self.root.get_screen('weather').ids.field,
            items=menu_items,
            position="bottom",
            width_mult=4,
        )
        self.menu.open()

    def build(self):
        global screen_manager
        screen_manager = ScreenManager()
        screen_manager.add_widget(screen=Builder.load_file("weather.kv"))
        screen_manager.add_widget(screen=Builder.load_string(settingsKV))
        return screen_manager

    def on_start(self):
        Window.bind(on_keyboard=on_key)
        self.weather_thread.start()
        self.current_date()

    def search_weather(self):
        default_location = self.return_default_loc()
        if default_location is None:
            print("No Default Location set")
            pass
        else:
            self.weather_forecast(default_location)

    def weather_forecast(self, city):
        try:
            query_type = 'current'

            BASE_URL = f"http://api.weatherapi.com/v1/{query_type}.json?key={self.API_KEY}&q={city}"

            URL = BASE_URL

            response = requests.get(URL)
            response = response.json()
            temp = response['current']['temp_c']
            humidity = response['current']['humidity']
            feels_like = response['current']['feelslike_c']
            status = response['current']['condition']['text']
            weather_icon = str(response['current']['condition']['icon']).split('/')[-1]
            pressure = response['current']['pressure_mb']
            wind_speed = response['current']['wind_kph']
            uv_index = response['current']['uv']

            self.display(temp, status, weather_icon, wind_speed, humidity, uv_index)

        except Exception as e:
            print(e)

        # Displaying The data In front
    @mainthread
    def display(self, temp, status, weather_icon, wind_speed, humidity, uv_index):
        self.root.get_screen('weather').ids.temp.text = str(round(temp))
        self.root.get_screen('weather').ids.status.text = str(status)
        self.root.get_screen('weather').ids.weather_icon.source = str(weather_icon)
        self.root.get_screen('weather').ids.wind.text = str(wind_speed) + ' Km/h'
        self.root.get_screen('weather').ids.humidity.text = str(humidity) + " %"
        self.root.get_screen('weather').ids.uv_index.text = str(uv_index)

    @staticmethod
    def change_screen():
        if screen_manager.current == 'weather':
            screen_manager.transition.direction = 'right'
            screen_manager.current = 'settings'
        else:
            screen_manager.transition.direction = 'left'
            screen_manager.current = 'weather'

    def current_date(self):
        day = today.day
        month = today.strftime('%B')
        week_day = today.strftime('%A')
        display_date = f"{week_day}\n{day}, {month}"
        self.root.get_screen('weather').ids.day.text = display_date


WeatherApp().run()
