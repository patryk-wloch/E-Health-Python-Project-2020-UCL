import logging.handlers
from getpass import getpass
from typing import Tuple
from tabulate import tabulate
from database import SQLQuery
from encryption import EncryptionHelper, PasswordHelper
from exceptions import DBRecordError
from iohandler import Parser

log_info = open('log/gp_system_info_log.log', 'a+')
log_debug = open('log/gp_system_debug_log.log', 'a+')
log_warning = open('log/gp_system_warning_log.log', 'a+')

fh_info = logging.handlers.RotatingFileHandler('log/gp_system_info_log.log', maxBytes=1000000, backupCount=2)
fh_info.setLevel(logging.INFO)  # change this If you need different level
fh_info.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(module)s - %(levelname)s - %(message)s'))

fh_debug = logging.handlers.RotatingFileHandler('log/gp_system_debug_log.log', maxBytes=1000000, backupCount=2)
fh_debug.setLevel(logging.DEBUG)  # change this If you need different level
fh_debug.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(module)s - %(levelname)s - %(message)s'))

fh_warning = logging.handlers.RotatingFileHandler('log/gp_system_warning_log.log', maxBytes=1000000, backupCount=2)
fh_warning.setLevel(logging.WARNING)  # change this If you need different level
fh_warning.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(module)s - %(levelname)s - %(message)s'))

main_logger = logging.getLogger("main")
main_logger.setLevel(logging.DEBUG)
main_logger.addHandler(fh_debug)
main_logger.addHandler(fh_info)
main_logger.addHandler(fh_warning)


class MenuHelper:
    """
    Helper class for initialising the main menu.
    Methods for login, registering and starting specific sub-functionalities
    """

    @staticmethod
    def login() -> Tuple[str, str]:
        """
        Login to a registered account.
        :return: username, user account type
        """
        main_logger.debug("Entered Login Sequence")
        for i in range(4, -1, -1):
            main_logger.debug(f"Username attempt {5 - i}")
            # limit to 5 username attempts
            try:
                # trying to get username
                try_username = Parser.string_parser("Please enter your username: ")
                main_logger.debug(f"UserName Entered: {try_username}")
                # retrieving the user if exist to compare to PW
                username_query = SQLQuery("SELECT username, passCode, Deactivated, UserType FROM Users "
                                          "WHERE username == ?").fetch_all(parameters=(try_username,))
                if len(username_query) != 1:
                    raise DBRecordError
                else:
                    username = try_username
                    login_array = username_query[0]
                    user_type = login_array[3]
                    Parser.print_clean("Username validated.")
                    main_logger.info(f"{try_username}, user valid")
                    break
            except DBRecordError:
                main_logger.warning("User doesn't exist or invalid")
                Parser.print_clean(f"Invalid Username: {i} attempts remaining")
        else:
            Parser.print_clean("You've entered an incorrect username too many times.")
            main_logger.critical("Too many failed Username attempts")
            Parser.user_quit()
        for i in range(4, -1, -1):
            try:
                # the PW is saved in hash so need to convert to hash to compare special parsing function because it will
                # hide the needed
                try_pw = PasswordHelper.hash_pw(getpass("Enter your password: "))
                if try_pw == login_array[1]:
                    Parser.print_clean("Password correct!")
                    if login_array[2] == "T":
                        Parser.print_clean("Your account is deactivated. Please contact the system administrator. ")
                        main_logger.critical(f"{username}, user deactivated, quitting.")
                        Parser.user_quit()
                    else:
                        return {"username": username, "user_type": user_type}
                else:
                    raise DBRecordError
            except DBRecordError:
                main_logger.warning("Password invalid")
                Parser.print_clean(f"Invalid Password: {i} attempts remaining")
        else:
            Parser.print_clean("You've entered an incorrect password too many times.")
            main_logger.critical("Too many failed Password attempts")
            Parser.user_quit()

    @staticmethod
    def register(admin=False) -> bool:
        """
        Register a new GP or Patient Account.
        """

        new_id, user_group = MenuHelper.get_id()
        if not new_id or not user_group:
            return False

        menu_helper = MenuHelper()
        username = menu_helper.get_check_username(user_group)
        password = menu_helper.register_new_password()
        birthday = menu_helper.get_birthday()
        Parser.print_clean("\n")

        first_name = menu_helper.get_name("first")
        Parser.print_clean("\n")

        last_name = menu_helper.get_name("last")
        Parser.print_clean("\n")

        telephone = menu_helper.valid_local_phone()
        address = menu_helper.get_address()
        Parser.print_clean("\n")

        postcode = menu_helper.valid_postcode()
        activation = "F" if admin else "T"
        login_count = 0

        insert_query = SQLQuery("INSERT INTO Users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)")
        insert_query.commit((new_id, username, password, birthday, first_name, last_name,
                             telephone, address, postcode, user_group, activation, login_count))

        Parser.print_clean("Successfully added account!")
        if not admin:
            print("If any incorrect details entered and for activation, contact an administrator.")
        Parser.handle_input()
        return True

    @staticmethod
    def help():
        Parser.print_clean("Welcome to Group 6 GP data management system.\n")
        print("Before using the system, you need to register for a GP or Patient account, and before logging in, "
              "it will need to be activated by one of the Administrator staff.\n")
        print("This application is a command line-based interface, and as such, you will need to navigate it with "
              "commands entered from the keyboard.\n")
        print("Wherever you are prompted to select an option from a list, simply type in the relevant letter and press "
              "Enter. These are not case-sensitive.\n")
        print("Where sizeable datasets are displayed for you, sometimes, a paging functionality will be used. To "
              "navigate the pages, enter A to go to the previous page, D to go to the next page, and C to exit the "
              "browse and proceed to further options.\n")
        print("You can logout at anytime by typing in --LOGOUT, or bring up this help function by typing in --HELP.\n")
        Parser.handle_input("Press Enter to return...")
        return

    @staticmethod
    def get_check_username(user_group) -> str:
        """
        :param str user_group: Patient or GP
        :return: New unique Username that is not currently being used
        """
        while True:
            parameter = Parser.string_parser("Please enter username of {0}: ".format(user_group))
            # check if it exists in table, if it does ask again
            exists_query = SQLQuery("SELECT 1 FROM Users WHERE username = '{0}'".format(parameter)) \
                .fetch_all()
            if exists_query or (parameter == ""):
                Parser.print_clean("username already exists. Please choose another.\n")
                continue
            else:
                Parser.print_clean("username approved.\n")
                return parameter

    @staticmethod
    def register_new_password() -> str:
        """
        :return: Check for valid new password
        """
        while True:
            Parser.print_clean("Any leading or trailing empty spaces will be removed.")
            password = getpass("Enter new password: ").strip()
            password_confirm = getpass("Enter new password again: ").strip()
            if (password != password_confirm) or (password == "") or (password_confirm == ""):
                print("Passwords do not match. Please try again.\n")
                continue
            else:
                print("Passwords Match.\n")
                return PasswordHelper.hash_pw(password)

    @staticmethod
    def get_address() -> str:
        """
        :return: Encrypted First line of GP or Patient UK address
        """
        return EncryptionHelper().encrypt_to_bits(
            Parser.string_parser("Please enter primary home address (one line): "))

    @staticmethod
    def get_name(name_type) -> str:
        """
        :param str name_type: First/Last Name flag for user input
        :return: Encrypted new first/last name of user
        """
        return EncryptionHelper().encrypt_to_bits(Parser.string_parser(
            "Please enter {0} name: ".format(name_type)))

    @staticmethod
    def get_birthday() -> str:
        """
        :return: Encrypted User birthday
        """
        return EncryptionHelper().encrypt_to_bits(str(Parser.date_parser("Please enter birthday: ",
                                                                         allow_back=False, allow_past=True)))

    @staticmethod
    def get_id() -> str:
        """
        :return: Valid user ID and type of user
        """
        while True:
            Parser.print_clean("Press --back to go back.")
            user_group = Parser.selection_parser(options={"A": "GP", "B": "Patient", "--back": "back"})
            if user_group == "--back":
                Parser.print_clean()
                return False, False
            elif user_group == "A":
                new_id = Parser.gp_no_parser()
                user_group = "GP"
                Parser.print_clean("\n")
                return new_id, user_group
            else:
                new_id = Parser.nhs_no_parser()
                user_group = "Patient"
                Parser.print_clean("\n")
                return new_id, user_group

    @staticmethod
    def valid_local_phone() -> str:
        """
        :return: return a valid UK phone number
        """
        while True:
            phone_number = Parser.string_parser("Please enter local UK phone number: ").strip()
            if (len(phone_number) == 11) and \
                    (not any([char in phone_number for char in ["+", "-", "(", ")"]])) and \
                    (not phone_number.isupper()) and (not phone_number.islower()):
                Parser.print_clean("Valid Phone Number.\n")
                return EncryptionHelper().encrypt_to_bits(phone_number)
            else:
                Parser.print_clean("Invalid Phone Number. Please try again.\n")

    @staticmethod
    def valid_postcode() -> str:
        """
        :return: return a valid UK postcode
        """
        while True:
            temp_postcode = Parser.string_parser("Please enter your postcode: ").strip().replace(" ", "")
            if not (5 <= len(temp_postcode) <= 8):
                Parser.print_clean("Invalid Postcode. Please try again.\n")
            else:
                Parser.print_clean("Valid Postcode.\n")
                return EncryptionHelper().encrypt_to_bits(temp_postcode)

    @staticmethod
    def dispatcher(username, user_type) -> None:
        """
        :param str username: Username of account
        :param str user_type: Type of account
        """
        main_logger.debug(f"Entered user session creation sequence with user: {username}; type {user_type}")
        if user_type == "Admin":
            from admin import Admin
            user = Admin(username)
            # this line is to make sure tat it entered the correct route
            main_logger.debug(f"{User} created using {user_type} method")
        elif user_type == "GP":
            from gp import GP
            user = GP(username)
            main_logger.debug(f"{User} created using {user_type} method")
        else:
            from patient import Patient
            user = Patient(username)
            main_logger.debug(f"{User} created using {user_type} method")
        main_logger.info(f"user: {username}; type {user_type}: logged in")
        if not user.handle_login_count():
            print("Error handling login.")
            Parser.user_quit()
        user.print_hello()
        user.print_information()
        user.main_menu()


class User:
    def __init__(self, username):
        """
        initializing user login process and return a User Object
        """
        self.username = username

        # retrieving the full information from DATAbase instead of just the password for authentication
        self.user_data = SQLQuery(
            "SELECT ID, username, firstName, lastName, phoneNo, HomeAddress, postCode, UserType, "
            "deactivated, birthday, LoginCount FROM Users WHERE username == ?").fetch_all(decrypter=EncryptionHelper(),
                                                                                          parameters=(username,))[0]
        # loading the user info into a state
        self.ID = self.user_data[0]
        self.username = self.user_data[1]
        self.first_name = self.user_data[2]
        self.last_name = self.user_data[3]
        self.phone_no = self.user_data[4]
        self.home_address = self.user_data[5]
        self.postcode = self.user_data[6]
        self.user_type = self.user_data[7]
        self.deactivated = self.user_data[8]
        self.birthday = self.user_data[9]
        self.login_count = self.user_data[10]

    def handle_login_count(self) -> bool:
        self.login_count += 1
        if self.login_count <= 1:
            if self.first_login():
                SQLQuery("UPDATE Users SET LoginCount = ? WHERE ID = ?").commit(parameters=(self.login_count, self.ID))
                return True
            else:
                return False
        else:
            SQLQuery("UPDATE Users SET LoginCount = ? WHERE ID = ?").commit(parameters=(self.login_count, self.ID))
            return True

    def print_hello(self) -> bool:
        """
        Personalised logged in message to user.
        """
        Parser.print_clean(f"Login Successful. Hello {self.first_name}")
        return True

    def print_information(self) -> bool:
        """
        Display all User information.
        """
        print(tabulate([("User Type:", self.user_type),
                        ("First Name: ", self.first_name),
                        ("Last Name: ", self.last_name),
                        ("Birthday: ", self.birthday),
                        ("Phone No: ", self.phone_no),
                        ("Home Address: ", self.home_address),
                        ("Post Code: ", self.postcode)
                        ]))
        return True

    def edit_information(self) -> None:
        while True:
            main_logger.info("Edit " + self.username)
            record_editor = Parser.selection_parser(options={"A": "Update Password", "B": "Update Birthday",
                                                             "C": "Update First Name", "D": "Update Last Name",
                                                             "E": "Update Phone Number", "F": "Update Home Address",
                                                             "G": "Update Postcode", "--back": "back"})

            menu = MenuHelper()
            if record_editor == "--back":
                Parser.print_clean()
                return
            elif record_editor == "A":
                new_parameter_value = menu.register_new_password()
                parameter = "passCode"
            elif record_editor == "B":
                new_parameter_value = menu.get_birthday()
                parameter = "birthday"
            elif record_editor == "C":
                new_parameter_value = menu.get_name("first")
                parameter = "firstName"
            elif record_editor == "D":
                new_parameter_value = menu.get_name("last")
                parameter = "lastName"
            elif record_editor == "E":
                new_parameter_value = menu.valid_local_phone()
                parameter = "phoneNo"
            elif record_editor == "F":
                new_parameter_value = menu.get_address()
                parameter = "HomeAddress"
            elif record_editor == "G":
                new_parameter_value = menu.valid_postcode()
                parameter = "postCode"
            try:
                from sqlite3 import DatabaseError
                SQLQuery("UPDATE Users SET {0} = ? WHERE username = ?".format(parameter)).commit((new_parameter_value,
                                                                                                  self.username))
                print("Parameter updated successfully!")
                main_logger.info("Updated record in database.")
            except DatabaseError:
                main_logger.warning("Database error!")
                print("Error updating the database!")


if __name__ == '__main__':
    """Main Program starts here."""

    # Exception handling if database not present/cannot connect
    import sqlite3
    try:
        main_logger.debug("Connecting to database...")
        from urllib.request import pathname2url
        database = 'file:{}?mode=rw'.format(pathname2url("GPDB.db"))
        conn = sqlite3.connect(database, uri=True)
        main_logger.debug("Connected to database")
    except sqlite3.OperationalError:
        main_logger.debug("Nonexistent Database present")
        Parser.print_clean("Database does not exist.")
        Parser.user_quit()

    while True:
        Parser.print_clean("Welcome to Group 6 GP System")
        option_selection = Parser.selection_parser(options={"R": "register", "L": "login", "H": "help",
                                                            "--quit": "quit"})

        if option_selection == 'L':
            main_logger.debug("Selected Login")
            current_user = MenuHelper.login()
            MenuHelper.dispatcher(current_user["username"], current_user["user_type"])
        elif option_selection == 'R':
            main_logger.debug("New user registration started")
            result = MenuHelper.register()
            Parser.user_quit()
        elif option_selection == "H":
            MenuHelper.help()
