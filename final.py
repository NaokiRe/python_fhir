import os

import keyboard
import subprocess
import time

from pynput import keyboard
from pynput import mouse

# Ignore the errors, this does actually work
import pyautogui

import tkinter as tk
from tkinter import filedialog, simpledialog
from PIL import Image, ImageTk, ImageGrab
import ironpdf
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import json
import secrets
import string
from datetime import datetime
import easyocr




# noinspection PyMethodMayBeStatic
# -- This is because it was annoying me
class systemInteractions:
    def __init__(self):
        self.__brew_dependencies = []
        self.dependencies_installed = self.install_dependencies(self.__brew_dependencies)

    def get_screen_size(self):
        return pyautogui.size()

    def run_command(self, command, isGlobal=False):
        if isGlobal:
            try:
                subprocess.run(args=["cd"])
            except subprocess.CalledProcessError as e:
                print("Couldn't enter global scope, executing in local directory instead")
        try:
            return subprocess.run(args=command, capture_output=True, check=True)
        except subprocess.CalledProcessError as e:
            raise e
            # returns the exception up for the code that ran the command to deal with right now
            # Could be modified to deal with exception internally

    def import_modules(self):
        try:
            import time
            import os
        except ImportError as e:
            print(f"uh oh, {e} just happened")

        # For modules that are not installed by default
        try:
            import keyboard
        except ImportError as e:
            self.run_command(["pip", "install", "keyboard"])
            import keyboard

        try:
            import pynput
            from pynput import mouse
            from pynput import keyboard
            from pynput.keyboard import Controller

        except ImportError as e:
            self.run_command(["pip", "install", "pynput"])
            import pynput
            from pynput import mouse
            from pynput import keyboard
            from pynput.keyboard import Controller, Listener

    def install_dependencies(self, brew_dependencies):
        failed = []

        self.import_modules()

        for dependency in brew_dependencies:
            try:
                self.run_command(["brew", "install", dependency])

            except subprocess.CalledProcessError as e:
                print(f"Installation of dependency {dependency} failed")
                failed.append([dependency, e])
                # Add code to deal with this in more detail later

        if failed:
            return False
        return True

    def quit(self, message):
        raise SystemExit(message)


class settings:
    # A settings object that any object with updatable settings should be able to access
    # It contains all the changeable values that a user should be able to modify
    def __init__(self, settings_file_path):
        if settings_file_path is None:
            # These are the defaults if no settings are provided
            self.__start_recording_key = '<cmd>+<shift>+e'
            self.__quit_thread_key = '<cmd>+<shift>+m'
            # As much as we could change this to an array, we have a fixed number of them and this is more readable
            self.__recording_period = 5.0

        else:
            self.__start_recording_key, self.__quit_thread_key, self.__recording_period = \
                self.get_settings(self.__path)

    def get_settings(self, path):
        pass

    def change_settings(self, path):
        pass

    def update_path(self, new_settings_path):
        self.__path = new_settings_path

    def get_keys(self):
        return self.__start_recording_key, self.__quit_thread_key

    def get_recording_period(self):
        return self.__recording_period


class finalityException(Exception):
    pass


class user_interaction:
    def __init__(self, settings_file_path):
        # self.start_recording_key = '<cmd>+<shift>+1'
        # self.quit_thread_key = '<cmd>+<shift>+2'
        # self.stop_hotkeys_key = '<shift>+<cmd>+2'
        self.start_recording_key = '<shift>+1'
        self.quit_thread_key = '<shift>+2'
        self.stop_hotkeys_key = '<shift>+3'
        self.hotkeys = self.get_hot_keys()
        self.keyTrackers()
        self.mouseTrackObj = None
        self.settings = settings(settings_file_path)
        self.systemInteractions = systemInteractions()
        self.rectangles_selected = []
        
        self.application_boundaries = [[0,0], [0,0]]
        # Not currently in use, but could bound mouse to the bounds of the application

    def get_hot_keys(self):
        return {self.start_recording_key: self.activate_recording,
        self.quit_thread_key: self.quit_thread,
        self.stop_hotkeys_key: self.stop_hotkeys}

    def start_up_mouse_tracking(self):
        self.mouseTrackObj = mouseTracker(self.settings)

    def activate_recording(self):
        print("Started recording")

        if self.mouseTrackObj is None:
            self.start_up_mouse_tracking()

        else:
            mouseRect = self.mouseTrackObj.select_rectangle()
            print(mouseRect)
            self.rectangles_selected.append(mouseRect)
            return mouseRect

    def stop_hotkeys(self):
        return False

    def quit_thread(self):
        print("Thread stopped")
        self.systemInteractions.quit(f"The quit hotkey ({self.quit_thread_key}) has been pressed")

    def keyTrackers(self):
        hotkeys = keyboard.GlobalHotKeys(self.hotkeys)
        hotkeys.start()

        # This is a blocking version
        # with keyboard.GlobalHotKeys(self.hotkeys) as hotkeys:
        #     hotkeys.join()


class mouseTracker:
    def __init__(self, settingsObj):
        self.settings_obj = settingsObj
        self.rectangle = []
        self.controller = mouse.Controller()


    def reset(self):
        # Resets the state before the tracker gets a rectangle
        self.rectangle = []

    def on_click(self, x, y, button, pressed):
        if pressed and button == mouse.Button.left:
            # Pressed down
            self.rectangle.append([x, y])
        elif button == mouse.Button.left:
            # Released
            self.rectangle.append([x, y])
            return False

    def return_last_rectangle(self):
        return sorted(self.rectangle, key=lambda point: [point[1], point[0]])

    def select_rectangle(self):
        self.reset()
        with mouse.Listener(on_click=self.on_click) as listener:
            listener.join()
        return self.return_last_rectangle()


# userInt = user_interaction(None)
# userInt.keyTrackers()
# while True:
#     print("Main loop is going on")
#     time.sleep(5)

class mongoDB:
    def __init__(self):
        # default set to admin account for testing purposes
        self.username = "admin"
        self.password = "admin987"
        self.database_url =   "fhirdatabase.f5gfwq3.mongodb.net"
        self.url = f"mongodb+srv://{self.username}:{self.password}@{self.database_url}/test?retryWrites=true&w=majority"
        # not using actual user credentials as MongoDB Atlas only allows up to 500 users, which is not enough for a real system
        # Also, cannot set directly from python -> have to use Atlas API using an admin account -> more secure to create an entire new program for this
        self.client = MongoClient(self.url, server_api=ServerApi("1"))

        # database
        self.login_details = self.client["login_details"]
        self.patient_data = self.client["patient_data"]
        # collections   
        self.doctors = self.login_details["doctors"]
        self.organisations = self.login_details["organisations"]

    def login(self, username, password):
        # check if user exists under login_details/doctors collection
        # if so, return True
        # else return False
        if self.doctors.find_one({"username": username, "password": password}):
            return True
        return False
    
    def signup(self, first_name, surname, username, password, organisation):
        # add user to login_details/doctors collection
        if self.doctors.find_one({"username": username}):
            return False
        self.doctors.insert_one({"first_name": first_name, "surname": surname, "username": username, "password": password, "organisation": organisation})
        return True
    
    def create_organisation(self, organisation, org_type):
        # add organisation to login_details/organisations collection
        # only for testing purposes -> admin account can create organisations
        if self.organisations.find_one({"organisation": organisation}):
            return False
        elif self.username == "admin":
            self.organisations.insert_one({"organisation": organisation, "type": org_type})
            # must add IP address to whitelist on MongoDB Atlas website
            return True
        
    def upload_patient_data(self, data, organisation):
        # add patient data to patient_data collection
        # only for testing purposes -> admin account can upload patient data
        if self.username == "admin":
            self.patient_data[organisation].insert_one(data)
            return True
        return False
    
    def upload_preset_data(self, preset, preset_name):
        # add preset data to patient_data collection
        # only for testing purposes -> admin account can upload preset data
        preset["name"] = preset_name
        if self.username == "admin":
            self.client["templates"]["pdf_templates"].insert_one(preset)
            return True
        return False
    
    def load_preset_data(self, preset_name):
        # get preset data from patient_data collection
        # only for testing purposes -> admin account can load preset data
        if self.username == "admin":
            return self.client["templates"]["pdf_templates"].find_one({"name": preset_name})
        return None
    
    def get_doctor_data(self, username):
        # get doctor data from login_details/doctors collection
        return self.doctors.find_one({"username": username})

class front_end:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Reading Application")

        self.current_pdf_path = None
        self.image_paths = []
        self.current_page = 0
        
        self.user_keylogger = user_interaction(None)

        self.db = mongoDB()
        self.preset_areas = {}

        self.field_options = ["status", "account_type", "first_name", "surname", "subject_display", "service_period_start",
                        "service_period_end", "coverage_reference", "owner_reference", "description"]
        self.extracted_data = {field: "" for field in self.field_options}

        self.login_frame = tk.Frame(self.root)
        self.signup_frame = tk.Frame(self.root)
        self.main_frame = tk.Frame(self.root)
        self.tab_frame = tk.Frame(self.root)

        self.signup_login_tab_widgets()
        self.create_login_widgets()
        self.create_signup_widgets()
        self.signup_frame.pack_forget()

    def create_login_widgets(self):
        '''
        Creates the widgets for the login frame
        '''
        self.login_frame.pack(padx=10, pady=10, side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.login_label = tk.Label(self.login_frame, text="Login", font=("Georgia", 16))
        self.login_label.pack(pady=10)

        self.username_label = tk.Label(self.login_frame, text="Username: ")
        self.username_label.pack(pady=5)

        self.username_entry = tk.Entry(self.login_frame)
        self.username_entry.pack(pady=5)

        self.password_label = tk.Label(self.login_frame, text="Password: ")
        self.password_label.pack(pady=5)

        self.password_entry = tk.Entry(self.login_frame, show="*")
        self.password_entry.pack(pady=5)

        self.login_button = tk.Button(self.login_frame, text="Login", command=self.login)
        self.login_button.pack(pady=5)
    
    def create_signup_widgets(self):
        '''
        Creates the widgets for the signup frame
        '''
        self.signup_frame.pack(padx=10, pady=10, side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.signup_label = tk.Label(self.signup_frame, text="Sign Up", font=("Georgia", 16))
        self.signup_label.pack(pady=10)

        self.signup_username_label = tk.Label(self.signup_frame, text="Username: ")
        self.signup_username_label.pack(pady=5)

        self.signup_username_entry = tk.Entry(self.signup_frame)
        self.signup_username_entry.pack(pady=5)

        self.signup_password_label = tk.Label(self.signup_frame, text="Password: ")
        self.signup_password_label.pack(pady=5)

        self.signup_password_entry = tk.Entry(self.signup_frame, show="*")
        self.signup_password_entry.pack(pady=5)

        self.first_name_label = tk.Label(self.signup_frame, text="First Name: ")
        self.first_name_label.pack(pady=5)

        self.first_name_entry = tk.Entry(self.signup_frame)
        self.first_name_entry.pack(pady=5)

        self.surname_label = tk.Label(self.signup_frame, text="Surname: ")
        self.surname_label.pack(pady=5)

        self.surname_entry = tk.Entry(self.signup_frame)
        self.surname_entry.pack(pady=5)

        self.organisation_label = tk.Label(self.signup_frame, text="Organisation: ")
        self.organisation_label.pack(pady=5)

        self.organisation_entry = tk.Entry(self.signup_frame)
        self.organisation_entry.pack(pady=5)

        self.signup_button = tk.Button(self.signup_frame, text="Sign Up", command=self.signup)
        self.signup_button.pack(pady=5)

    def signup_login_tab_widgets(self):
        '''
        Creates the widgets for the tab which will cycle between the login and signup frames
        '''
        self.tab_frame.pack(padx=10, pady=10, side=tk.LEFT, fill=tk.BOTH, expand=True)

        # add login and signup buttons
        self.login_tab = tk.Button(self.tab_frame, text="Login", command=lambda: self.switch_signup_login("Login"))
        self.login_tab.pack(side=tk.LEFT, padx=5, pady=5)

        self.signup_tab = tk.Button(self.tab_frame, text="Sign Up", command=lambda: self.switch_signup_login("Signup"))
        self.signup_tab.pack(side=tk.LEFT, padx=5, pady=5)

    def create_data_option_widets(self):
        # create widgets to specify the field to extract
        # fields are: status, account_type, first_name, surname, subject_display, service_period_start, 
        # service_period_end, coverage_reference, owner_reference, description

        # widget to select the field to extract
        self.field_label = tk.Label(self.root, text="Select Field to Extract: ")
        self.field_label.pack(pady=5)


        self.field_selected = tk.StringVar(self.root)
        self.field_selected.set(self.field_options[0])
        self.field_menu = tk.OptionMenu(self.root, self.field_selected, *self.field_options)
        self.field_menu.pack(pady=5)

        # widget to show the list of fields already extracted
        self.extracted_fields_label = tk.Label(self.root, text="Extracted Fields: ")
        self.extracted_fields_label.pack(pady=5)

        self.extracted_fields_listbox = tk.Listbox(self.root, selectmode=tk.SINGLE)
        self.extracted_fields_listbox.pack(pady=5)

        # widget to name preset rectangles
        self.preset_name_label = tk.Label(self.root, text="Preset Name: ")
        self.preset_name_label.pack(pady=5)

        self.preset_name_entry = tk.Entry(self.root)
        self.preset_name_entry.pack(pady=5)

        # widget to save the preset rectangles
        self.save_preset_button = tk.Button(self.root, text="Save Preset", command=self.save_preset)
        self.save_preset_button.pack(pady=5)

        # widget to load preset rectangles
        self.load_preset_button = tk.Button(self.root, text="Load Preset", command=self.load_preset)
        self.load_preset_button.pack(pady=5)

        # widget to upload current rectangles to folder of pdf
        self.upload_preset_button = tk.Button(self.root, text="Multi-pdf scan", command=self.multi_scan)
        self.upload_preset_button.pack(pady=5)


    def save_preset(self):
        # save the preset to the database
        if self.db.upload_preset_data(self.preset_areas, self.preset_name_entry.get()):
            tk.messagebox.showinfo("Preset Saved", "Preset has been saved to the database")
        else:
            tk.messagebox.showwarning("Preset Not Saved", "Preset could not be saved to the database")

    def load_preset(self):
        # load the preset from the database
        if preset := self.db.load_preset_data(self.preset_name_entry.get()):
            self.preset_areas = preset
            for field in self.preset_areas:
                self.extracted_fields_listbox.insert(tk.END, field)
            tk.messagebox.showinfo("Preset Loaded", "Preset has been loaded from the database")

    def multi_scan(self):
        # scan multiple pdfs in a folder
        # get the folder path
        folder_path = filedialog.askdirectory()
        if folder_path:
            for file in os.listdir(folder_path):
                if file.endswith(".pdf"):
                    self.current_pdf_path = os.path.join(folder_path, file)
                    # convert and display images
                    self.convert_and_display_images()
                    # extract all fields
                    self.extract_all_fields()
                    # upload to database
                    self.upload_to_database()

    def switch_signup_login(self, next_tab):
        '''
        Switches between the login and signup frames
        '''
        self.login_frame.pack_forget()
        self.signup_frame.pack_forget()
        if next_tab == "Login":
            self.login_frame.pack()
        else:
            self.signup_frame.pack()

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        print(f"Username: {username}, Password: {password}")
        if self.db.login(username, password):
            self.login_frame.pack_forget()
            self.signup_frame.pack_forget()
            self.tab_frame.pack_forget()
            self.create_main_widgets()
            self.create_data_option_widets()
        else:
            tk.messagebox.showwarning("Invalid Login", "Username or password is incorrect")
    
    def signup(self):
        username = self.signup_username_entry.get()
        password = self.signup_password_entry.get()
        first_name = self.first_name_entry.get()
        surname = self.surname_entry.get()
        organisation = self.organisation_entry.get()
        if self.db.signup(first_name, surname, username, password, organisation):
            self.login_frame.pack_forget()
            self.signup_frame.pack_forget()
            self.tab_frame.pack_forget()
            self.create_main_widgets()
            self.create_data_option_widets()
        else:
            tk.messagebox.showwarning("Invalid Signup", "Username already exists")


    def create_main_widgets(self):
        self.label = tk.Label(self.root, text="PDF Reading Application", font=("Georgia", 16))
        self.label.pack(pady=10)

        self.select_button = tk.Button(self.root, text="Select PDF", command=self.select_pdf)
        self.select_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.prev_button = tk.Button(self.root, text="Previous Page", command=self.turn_page_back,
                                     state=tk.DISABLED)
        self.prev_button.pack(side=tk.LEFT, padx=5, pady=5)
        # Can't be selected until the pdf has been selected

        self.next_button = tk.Button(self.root, text="Next Page", command=self.turn_page_forward, state=tk.DISABLED)
        self.next_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.goto_button = tk.Button(self.root, text="Go to Page", command=self.turn_to_specific_page, state=tk.DISABLED)
        self.goto_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.exit_button = tk.Button(self.root, text="Exit", command=self.root.quit)
        self.exit_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.save_button = tk.Button(self.root, text="Save Selected", command=self.get_last_rectangle)
        self.save_button.pack(side=tk.LEFT, padx=5, pady=5)

        # widget to upload to database
        self.upload_button = tk.Button(self.root, text="Upload to Database", command=self.upload_to_database)
        self.upload_button.pack(side=tk.LEFT, padx=5, pady=5)


        self.image_frame = tk.Frame(self.root)
        self.image_frame.pack(padx=10, pady=10, side=tk.LEFT, fill=tk.BOTH, expand=True)

    def create_fhir_record(self):
        # create a FHIR record from the extracted data
        doctor_data = self.db.get_doctor_data(self.db.username)
        return self.create_fhir_account(self.extracted_data["status"], self.extracted_data["account_type"], "patient billing account",
                                        f"{self.extracted_data['first_name']} {self.extracted_data['surname']}", self.extracted_data["surname"],
                                        self.extracted_data["first_name"], self.extracted_data["service_period_start"], self.extracted_data["service_period_end"],
                                        self.extracted_data["coverage_reference"], self.extracted_data["owner_reference"], self.extracted_data["description"],
                                        doctor_data["organisation"], doctor_data["username"], doctor_data["first_name"], doctor_data["surname"])

    def generate_random_id(self, length=40):
        characters = string.ascii_letters + string.digits + string.punctuation
        return ''.join(secrets.choice(characters) for _ in range(length))

    def create_fhir_account(self, identifier, status, account_type, name, patient_surname, patient_firstname, service_period_start, service_period_end, coverage_reference, owner_reference, description, organization_id, doctor_id, doctor_firstname, doctor_surname):
        last_updated = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

        account = {
            "resourceType": "Account",
            "id": self.generate_random_id(),
            "text": {
                "status": "generated",
                "div": f"<div xmlns='http://www.w3.org/1999/xhtml'>{name}</div>"
            },
            "identifier": [
                {
                    "system": "urn:oid:0.1.2.3.4.5.6.7",
                    "value": identifier if identifier else self.generate_random_id(40)
                }
            ],
            "status": status,
            "type": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                        "code": account_type,
                        "display": "patient billing account"
                    }
                ],
                "text": "patient"
            },
            "name": name,
            "subject": {
                "reference": "Patient/example",
                "display": f"{patient_surname} {patient_firstname}"
            },
            "servicePeriod": {
                "start": service_period_start,
                "end": service_period_end
            },
            "coverage": [
                {
                    "coverage": {
                        "reference": coverage_reference
                    },
                    "priority": 1
                }
            ],
            "owner": {
                "reference": f"Organization/{owner_reference}",
                "identifier": {
                    "value": organization_id
                }
            },
            "description": description,
            "generalPractitioner": [
                {
                    "identifier": {
                        "value": doctor_id
                    },
                    "name": {
                        "family": doctor_surname,
                        "given": [doctor_firstname]
                    }
                }
            ],
            "meta": {
                "tag": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ActReason",
                        "code": "HTEST",
                        "display": "test health data"
                    }
                ],
                "versionId": "1",
                "lastUpdated": last_updated
            }
        }

        return account
         
    def upload_to_database(self):
        # upload the extracted data to the database
        fhir_json = self.create_fhir_record()
        if self.db.upload_patient_data(fhir_json, self.db.username):
            tk.messagebox.showinfo("Data Uploaded", "Data has been uploaded to the database")
        else:
            tk.messagebox.showwarning("Data Not Uploaded", "Data could not be uploaded to the database")

    def img_to_str(self, img_path):
        reader = easyocr.Reader(['en'])
        result = reader.readtext(img_path)
        return result

    def extract_all_fields(self):
        for (field, (page, rect)) in self.preset_areas.items():
            self.extracted_data[field] = self.img_to_str(f"./{page}_imgs/{page}_{field}.png")

    def convert_pdf_to_images(self, pdf_file):
        # For big PDF's, this can lag a lot. Ps got this from some tutorial
        pdf = ironpdf.PdfDocument.FromFile(pdf_file)

        # Extract all pages to a folder as image files
        folder_path = "images"
        pdf.RasterizeToImageFiles(os.path.join(folder_path, "*.png"))

        # Get the list of image files in the folder
        image_paths = []
        for filename in sorted(os.listdir(folder_path), key=lambda x: int(x.split('.')[0])):
            if filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
                image_paths.append(os.path.join(folder_path, filename))
        return image_paths
    
    def get_last_rectangle(self):
        if self.user_keylogger.rectangles_selected:
            rect = self.user_keylogger.rectangles_selected[-1]
            self.preset_areas[self.field_selected.get()] = (self.current_page, rect)
            self.extract_snippet(rect, [self.field_selected.get()])
            self.extracted_fields_listbox.insert(tk.END, self.field_selected.get())
        else:
            tk.messagebox.showwarning("No Rectangle Selected", "Please select a rectangle to extract")
                    

    def select_pdf(self):
        self.clear_image_folder()
        self.current_pdf_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if self.current_pdf_path:
            self.convert_and_display_images()

    def convert_and_display_images(self):
        self.image_paths = self.convert_pdf_to_images(self.current_pdf_path)

        if self.image_paths:
            self.current_page = 0
            self.show_current_page()

    def show_current_page(self):
        print(self.image_paths)
        if self.image_paths:
            self.prev_button.config(state=tk.NORMAL if self.current_page > 0 else tk.DISABLED)
            self.next_button.config(state=tk.NORMAL if self.current_page < len(self.image_paths) - 1 else tk.DISABLED)
            # Fairly explanatory, but just checks that there is a previous and next page to access or else it's disabled
            self.goto_button.config(state=tk.NORMAL)

            for widget in self.image_frame.winfo_children():
                widget.destroy()

            img_path = self.image_paths[self.current_page]
            image = Image.open(img_path)

            # The image wouldn't fit in the bounds so i resized it
            max_width = self.root.winfo_screenwidth() * 0.75
            max_height = self.root.winfo_screenheight() * 0.75
            image.thumbnail((max_width, max_height))
            photo = ImageTk.PhotoImage(image)
            label = tk.Label(self.image_frame, image=photo)
            label.image = photo
            label.pack(pady=5)

    def turn_page_back(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.show_current_page()

    def turn_page_forward(self):
        if self.current_page < len(self.image_paths) - 1:
            self.current_page += 1
            self.show_current_page()

    def turn_to_specific_page(self):
        target_page = simpledialog.askinteger("Which page do you want to turn to?", f"Enter the page number, "
                                                f"from 1 to {len(self.image_paths)}: ", parent=self.root)
        if target_page is not None and 1 <= target_page <= len(self.image_paths):
            self.current_page = target_page - 1
            self.show_current_page()

        else:
            tk.messagebox.showwarning("Invalid Page", f"Page number should be between 1 and {len(self.image_paths)}")


    def clear_image_folder(self):
        # This clears all of the images from the current Images folder, which prevents reading into previous gen pdf slides
        directory_path = "images"#os.getcwd()
        for file in os.listdir(directory_path):
            file_path = os.path.join(directory_path, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except OSError as e:
                print(f"Path {file_path} is inaccessible", e)

    def extract_snippet(self, rectangle_coords: tuple[tuple[int, int], tuple[int, int]], field: str):
        # open the document
        # doc = fitz.open(f"images/{self.current_page + 1}.png")
        # #assume first page for now
        # doc = doc[0]
        # top_left, bottom_right = rectangle_coords
        # clip = (top_left[0], top_left[1], bottom_right[0], bottom_right[1])
        # clipped_img = doc.get_pixmap(clip=clip)
        # directory = f"./field_imgs"
        # if not os.path.exists(directory):
        #     os.makedirs(directory)
        # clipped_img.save(f"./field_imgs/{field}.png")
        
        # take a screenshot using pyautogui
        left, top, right, bottom = rectangle_coords[0][0], rectangle_coords[0][1], rectangle_coords[1][0], rectangle_coords[1][1]
        width, height = right - left, bottom - top
        screenshot = pyautogui.screenshot(region=(left, top, width, height))
        screenshot.save(f"./field_imgs/{field}.png")

if __name__ == "__main__":
    root = tk.Tk()
    app = front_end(root)
    root.mainloop()