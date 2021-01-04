from tabulate import tabulate
from main import User, MenuHelper
from encryption import EncryptionHelper
from iohandler import Parser
from iohandler import Paging
from database import SQLQuery
import datetime
from exceptions import DBRecordError

print_clean = Parser.print_clean
delta = datetime.timedelta
date_now = datetime.datetime.now().date()
dtime_now = datetime.datetime.now()
strptime = datetime.datetime.strptime


class Patient(User):
    """
    patient Class with navigation options and various functionalities.
    """

    def main_menu(self) -> None:
        """
        Main Menu for Patient-type users.
        """
        while True:
            print("You're currently viewing main menu options for Patient {}.".format(self.username))
            option_selection = Parser.selection_parser(
                options={"B": "book appointments", "I": "view upcoming appointments",
                         "C": "cancel an appointment", "R": "review/rate appointments",
                         "--logout": "Logout"})
            if option_selection == "--logout":
                # Quitting is required for logout to ensure all personal data is cleared from session
                print_clean("Logging you out...")
                Parser.user_quit()
            elif option_selection == "B":
                self.book_appointment_start()
            elif option_selection == "I":
                self.check_in_appointment()
            elif option_selection == "C":
                self.cancel_appointment()
            elif option_selection == "R":
                r_selection = Parser.selection_parser(options={"A": "review", "B": "rate", "--back": "back"})
                if r_selection == "--back":
                    continue
                elif r_selection == "A":
                    self.review_appointment()
                elif r_selection == "B":
                    self.rate_appointment()

    def book_appointment_start(self):
        """
        choose a date -- choose a GP
        --choose time
        --give random number as bookingNo
        --move from available_time
        --insert in visit
        """
        while True:
            result_table = self.fetch_format_appointments(date_now + delta(days=1), 8)
            print("You are viewing all available appointments for the next week. To view appointments up "
                               "to 2 weeks ahead, use 'select by date' or 'select by GP' options below")
            if not result_table:
                return False


            headersholder = ["Pointer", "GP Name", "Last Name", "Timeslot"]
            result_index = 4

            Paging.show_page(1, result_table, 5, result_index, headersholder)


            print("How would you like to choose? ")
            booking_selection = Parser.selection_parser(
                options={"E": "select earliest available appointment",
                         "G": "select by GP", "D": "select by date", "--back": "back"})
            if booking_selection == "E":
                if self.process_booking(result_table[0]):
                    return True
            if booking_selection == "D":
                if self.book_appointment_date():
                    return True
            elif booking_selection == "G":
                if self.book_appointment_gp():
                    return True
            elif booking_selection == "--back":
                Parser.print_clean()
                return False

    @staticmethod
    def fetch_format_appointments(selected_date, selected_delta=1, GP_ID='%'):
        result = SQLQuery("SELECT firstName, lastName, Timeslot, available_time.StaffID FROM "
                          "(available_time JOIN Users ON available_time.StaffID = Users.ID) WHERE "
                          "available_time.StaffID LIKE ? AND Timeslot >= ? AND Timeslot <= ? ORDER BY Timeslot"
                          ).fetch_all(parameters=(GP_ID, selected_date, selected_date + delta(days=selected_delta)),
                                      decrypter=EncryptionHelper())
        if len(result) == 0:
            print(f"There are no available appointments matching the search criteria. ")
            Parser.handle_input("Press Enter to continue.")
            return False
        result_table = []
        for count, item in enumerate(result):
            result_table.append([count + 1, item[0], item[1], item[2], item[3]])
        return result_table

    def book_appointment_date(self):
        while True:
            selected_date = Parser.date_parser(question=f"Managing for Patient {self.username}.\n"
                                                        "Select a Date:\n")
            if selected_date == "--back":
                print_clean()
                return False
            result_table = self.fetch_format_appointments(selected_date)
            if not result_table:
                continue
            print(f"You are viewing all available appointments for: {selected_date}")
            print(tabulate([result[0:4] for result in result_table], headers=["Pointer", "GP Name", "Last Name",
                                                                              "Timeslot"]))
            selected_appointment = Parser.list_number_parser("Select an appointment by the Pointer.",
                                                             (1, len(result_table)), allow_multiple=False)
            if selected_appointment == '--back':
                return False
            selected_row = result_table[selected_appointment - 1]
            if self.process_booking(selected_row):
                return True

    def book_appointment_gp(self):
        while True:
            gp_result = SQLQuery("SELECT users.firstName, users.lastName, GP.Introduction, GP.ClinicAddress, "
                                 "GP.ClinicPostcode, GP.Gender, GP.Rating, users.ID FROM (GP INNER JOIN users ON "
                                 "GP.ID = users.ID) WHERE users.ID IN ( SELECT DISTINCT StaffID FROM available_time "
                                 "WHERE Timeslot >= ? AND Timeslot <= ? )"
                                 ).fetch_all(parameters=(date_now + delta(days=1), date_now + delta(days=15)),
                                             decrypter=EncryptionHelper())
            gp_table = []
            for count, item in enumerate(gp_result):
                gp_table.append([count + 1, item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7]])
            if len(gp_table) == 0:
                print("There are no GPs in the system yet.")
                Parser.handle_input("Press Enter to continue...")
                return False
            Parser.print_clean(f"You are viewing all available GPs in 2 weeks from: {date_now} ")
            print(tabulate([gp[0:8] for gp in gp_table], headers=["Pointer", "First Name", "Last Name", "Introduction",
                                                                  "Clinic Address", "Clinic Postcode",
                                                                  "Gender", "Rating"]))
            selected_gp_pointer = Parser.list_number_parser("Select GP by the Pointer.",
                                                            (1, len(gp_table)), allow_multiple=False)
            if selected_gp_pointer == '--back':
                return False
            selected_gp = gp_table[selected_gp_pointer - 1][8]
            result_table = self.fetch_format_appointments(date_now + delta(days=1), 15, selected_gp)
            if not result_table:
                continue
            print(f"You are viewing appointments for the selected GP:")
            print(tabulate([result[0:4] for result in result_table], headers=["Pointer", "GP First Name",
                                                                              "Last Name", "Timeslot"]))
            selected_appointment = Parser.list_number_parser("Select an appointment by the Pointer.",
                                                             (1, len(result_table)), allow_multiple=False)
            if selected_appointment == '--back':
                return False
            selected_row = result_table[selected_appointment - 1]
            if self.process_booking(selected_row):
                return True

    def process_booking(self, selected_row):
        encrypt = EncryptionHelper().encrypt_to_bits
        while True:
            Parser.print_clean("This is time slot will be booked by you:")
            print("GP: {} {}".format(selected_row[1], selected_row[2]))
            print("Timeslot: {}\n".format(selected_row[3]))
            confirm = Parser.selection_parser(options={"Y": "Confirm", "N": "Go back and select again"})
            # Confirm if user wants to delete slots
            if confirm == "Y":
                try:
                    SQLQuery("BEGIN TRANSACTION; INSERT INTO Visit (NHSNo, StaffID, Timeslot, Confirmed, Attended) "
                             f"VALUES ({self.ID}, '{selected_row[4]}', '{selected_row[3]}', 'P', 'F'); "
                             f"DELETE FROM available_time WHERE StaffID = '{selected_row[4]}'"
                             f" AND TIMESLOT = '{selected_row[3]}'; COMMIT"
                             ).commit(multiple_queries=True)
                    print("Booked successfully.")
                    visit_result = SQLQuery("SELECT BookingNo, NHSNo, firstName, lastName, Timeslot FROM "
                                            "(Visit JOIN Users ON VISIT.StaffID = Users.ID)"
                                            "WHERE Timeslot = ? AND StaffID = ? "
                                            ).fetch_all(parameters=(selected_row[3], selected_row[4]),
                                                        decrypter=EncryptionHelper())
                    booking_no = visit_result[0][0]
                    print(tabulate(visit_result,
                                   headers=["BookingNo", "NHSNo", "GP First Name", "Last Name", "Timeslot"]))
                    Parser.handle_input("Press Enter to continue...")
                except DBRecordError:
                    print("Error encountered")
                    Parser.handle_input("Press Enter to continue...")
                    return False
                info_input = encrypt(Parser.string_parser("Please enter your notes for GP before the visit: "))
                SQLQuery("UPDATE Visit SET PatientInfo = ? WHERE BookingNo = ? "
                         ).commit((info_input, booking_no))
                print("Your information have been recorded successfully!")
                Parser.handle_input("Press Enter to continue...")
                Parser.print_clean()
                return True
            else:
                print("Booking cancelled.")
                Parser.handle_input("Press Enter to continue...")
                Parser.print_clean()
                return False

    def check_in_appointment(self):
        """
            show all booking
            if time later, allow to check in
            change attend to T
            """
        stage = 0
        while stage == 0:
            appointments = SQLQuery("SELECT bookingNo, NHSNo, firstName, lastName, Timeslot, Confirmed, StaffID FR"
                                    "OM (visit JOIN Users ON visit.StaffID = Users.ID) WHERE NHSNo = ? AND Attended"
                                    " = ? AND Timeslot >= ? "
                                    ).fetch_all(parameters=(self.ID, "F", dtime_now - delta(hours=1)),
                                                decrypter=EncryptionHelper())

            confirmed_appointments = list(enumerate([appt for appt in appointments if appt[5] == "T"], 1))
            pending_appointments = list(enumerate([appt for appt in appointments if appt[5] == "P"], 1))
            rejected_appointments = list(enumerate([appt for appt in appointments if appt[5] == "F"], 1))
            Parser.print_clean("You are viewing all your booked appointments: ")

            if not appointments:
                print("You have not booked any appointments.")
                Parser.handle_input()
                return False

            if confirmed_appointments:
                print("Confirmed appointments:")
                print(tabulate([[count] + appointment[0:5] for count, appointment in confirmed_appointments],
                               headers=["Pointer", "BookingNo", "NHSNo", "GP Name", "Last Name", "Timeslot"]))
            if pending_appointments:
                print("Pending appointments - wait for confirmation or change appointment:")
                print(tabulate([[count] + appointment[0:5] for count, appointment in pending_appointments],
                               headers=["Pointer", "BookingNo", "NHSNo", "GP Name", "Last Name", "Timeslot"]))
            if rejected_appointments:
                print("Rejected appointments:")
                print(tabulate([[count] + appointment[0:5] for count, appointment in rejected_appointments],
                               headers=["Pointer", "BookingNo", "NHSNo", "GP Name", "Last Name", "Timeslot"]))

            print("")
            option_selection = Parser.selection_parser(
                options={"I": "check in confirmed appointment", "C": "change appointment", "--back": "back"})
            if option_selection == "--back":
                return
            elif option_selection == "C":
                return
            elif option_selection == "I":
                stage = 1

        while stage == 1:
            Parser.print_clean("You can only check in within an hour of a scheduled confirmed appointment.")
            check_appt = list(enumerate([appt for appt in appointments if dtime_now - delta(hours=1) <=
                                         strptime(appt[4], '%Y-%m-%d %H:%M:%S') <= dtime_now + delta(hours=1)], 1))
            if not check_appt:
                Parser.handle_input("Press Enter to continue...")
                stage = 0
                continue
            print(tabulate([[count] + appointment[0:5] for count, appointment in check_appt],
                           headers=["Pointer", "BookingNo", "NHSNo", "GP Name", "Last Name", "Timeslot"]), "\n")

            selected_appointment = Parser.list_number_parser("Select an appointment by the Pointer.",
                                                             (1, len(check_appt)), allow_multiple=False)
            if selected_appointment == '--back':
                stage = 0
                continue
            else:
                appointment_check_in = check_appt[selected_appointment - 1][1]
                print("This is the appointment you are checking in for: \n ")
                print(tabulate([appointment_check_in[0:5]], headers=["BookingNo", "NHSNo", "GP Name",
                                                                     "Last Name", "Timeslot"]), "\n")
                confirm = Parser.selection_parser(options={"Y": "check-in", "N": "cancel check-in"})
                if confirm == "Y":
                    try:
                        SQLQuery("UPDATE Visit SET Attended = 'T' WHERE BookingNo = ? "
                                 ).commit((appointment_check_in[0],))
                        print("You have been checked in successfully!.")
                        Parser.handle_input("Press Enter to continue...")
                        return True
                    except DBRecordError:
                        print("Error encountered")
                        Parser.handle_input("Press Enter to continue...")
                else:
                    print("Removal cancelled.")
                    Parser.handle_input("Press Enter to continue...")
                    stage = 0

    def cancel_appointment(self):
        """
            bookings can be cancelled five days in advance
            move from visit
            insert in available time
            """
        stage = 0
        while stage == 0:
            valid_cancel = SQLQuery("SELECT BookingNo, NHSNo, lastName, Timeslot, PatientInfo, StaffID FROM (visit "
                                    "JOIN Users on visit.StaffID = Users.ID) WHERE NHSNo = ? AND Timeslot >= ?"
                                    ).fetch_all(parameters=(self.ID, dtime_now + delta(days=5)),
                                                decrypter=EncryptionHelper())
            appointments_table = []
            for count, appt in enumerate(valid_cancel, 1):
                appointments_table.append([count, appt[0], appt[1], appt[2], appt[3], appt[4], appt[5]])
            Parser.print_clean(f"You are viewing all the appointments can be cancelled.")
            if not appointments_table:
                print(f"No Appointments can be cancelled.\n")
                return
            else:
                stage = 1

        while stage == 1:
            print(tabulate([appt[0:6] for appt in appointments_table],
                           headers=["Pointer", "BookingNo", "NHSNo", "GP Name", "Timeslot", "Patient Info"]))
            selected_cancel_appointment = Parser.list_number_parser("Select an appointment to cancel by the Pointer.",
                                                                    (1, len(appointments_table)), allow_multiple=False)
            selected_row = appointments_table[selected_cancel_appointment - 1]
            Parser.print_clean("This is appointment you want to cancel:")
            print(tabulate([selected_row], headers=["Pointer", "BookingNo", "NHSNo", "Timeslot", "Patient Info"]))
            confirmation = Parser.selection_parser(options={"Y": "Confirm", "N": "Go back and select again"})

            if confirmation == "Y":
                try:
                    SQLQuery("DELETE FROM visit WHERE BookingNo = ?").commit(parameters=(selected_row[1],))
                    SQLQuery("INSERT INTO available_time VALUES (?,?)").commit(parameters=(selected_row[6],
                                                                                           selected_row[4]))
                    print("Appointment is cancelled successfully.")
                except Exception as e:
                    print("Database Error...", e)
            else:
                Parser.print_clean()
                return

    def review_appointment(self):
        while True:
            record_viewer = Parser.selection_parser(
                options={"A": "Review past appointments", "B": "Review prescriptions",
                         "--back": "back"})
            if record_viewer == "--back":
                Parser.print_clean("\n")
                return False

            elif record_viewer == "A":
                query_string = "SELECT visit.BookingNo, visit.NHSNo, users.firstName, users.lastName, " \
                               "visit.Timeslot, visit.PatientInfo, visit.Confirmed, visit.Attended, visit.Rating " \
                               "FROM (visit INNER JOIN users ON visit.StaffID = users.ID) WHERE visit.NHSNo = ? "
                headers = ("BookingNo", "NHSNo", "GP First Name", "Last", "Timeslot",
                           "Patient Info", "Confirmed", "Attended", "Rating")
            else:
                query_string = "SELECT prescription.BookingNo, users.firstName, users.lastName, " \
                               "visit.PatientInfo, visit.Diagnosis, prescription.drugName, " \
                               "prescription.quantity, prescription.Instructions " \
                               "FROM (visit INNER JOIN users ON visit.StaffID = users.ID) " \
                               "INNER JOIN prescription ON " \
                               "visit.BookingNo = prescription.BookingNo WHERE visit.NHSNo = ? "

                headers = ("BookingNo", "GP Name", "Last Name", "Patient Info", "Diagnosis",
                           "Drug Name", "Quantity", "Instructions", "Notes")

            query = SQLQuery(query_string)
            all_data = query.fetch_all(decrypter=EncryptionHelper(), parameters=(self.ID,))

            if len(list(all_data)) == 0:
                Parser.print_clean("No records Available.\n")
            else:
                print(tabulate(all_data, headers))

    def rate_appointment(self):
        stage = 0
        while stage == 0:
            patient_result = SQLQuery("SELECT bookingNo, firstName, lastName, Timeslot, Rating, StaffID FROM (Visit "
                                      "JOIN Users on Visit.StaffID = Users.ID) WHERE NHSNo = ? AND Attended = 'T' "
                                      ).fetch_all(parameters=(self.ID,), decrypter=EncryptionHelper())

            appointments_table = []
            if not patient_result:
                print(f"You don't have any attended appointment")
                input("Press Enter to continue...")
                return False

            for count, appt in enumerate(patient_result, 1):
                appointments_table.append([count, appt[0], appt[1], appt[2], appt[3], appt[4], appt[5]])

            Parser.print_clean("These are appointments you have attended:")
            print(tabulate([appt[0:6] for appt in appointments_table],
                           headers=["Pointer", "BookingNo", "GP Name", "Last Name", "Timeslot", "Rating"]))
            print("Your opinion matters to us. Please take the time to rate your experience with our GP.")

            selected_appt = Parser.list_number_parser("Select an appointment to rate by the Pointer.",
                                                      (1, len(appointments_table)), allow_multiple=False)
            if selected_appt == "--back":
                print_clean()
                return False

            selected_row = appointments_table[selected_appt - 1]
            selected_rate = int(Parser.list_number_parser("Select a rating between 1-5. ", (1, 5))[0])
            try:
                current_rate = int(SQLQuery("SELECT Rating FROM GP WHERE ID = ?").fetch_all(parameters=(selected_row[6],))[0][0])
                rate_count = int(SQLQuery("SELECT COUNT(Rating) FROM Visit WHERE StaffID = ?"
                                      ).fetch_all(parameters=(selected_row[6],))[0][0])
                print(current_rate)
                print(rate_count)
                if current_rate != 0:
                    new_rate = round((((current_rate*rate_count) + selected_rate) / (rate_count + 1)), 2)
                else:
                    new_rate = selected_rate

                SQLQuery("UPDATE Visit SET Rating = ? WHERE BookingNo = ? ").commit((selected_rate, selected_row[1]))
                SQLQuery("UPDATE GP SET Rating = ? WHERE ID = ? ").commit((new_rate, selected_row[6]))
                print("Your rating has been recorded successfully!")
                Parser.handle_input("Press Enter to continue...")
                stage = 0

            except DBRecordError:
                print("Error encountered")
                input("Press Enter to continue...")

    def first_login(self):
        Parser.print_clean("Welcome Patient {}. This is your first login. ".format(self.username))
        print("You need to input additional information before you can proceed.")
        Parser.handle_input("Press Enter to continue...")
        encrypt = EncryptionHelper().encrypt_to_bits
        Parser.print_clean("Enter your gender: ")
        gender = Parser.selection_parser(options={"M": "Male", "F": "Female", "N": "Do not disclose"})
        info = encrypt(Parser.string_parser("Enter an intro paragraph about yourself: "))
        notice = encrypt(Parser.string_parser("Enter any allergies or important medical history: "))
        try:
            SQLQuery("INSERT INTO Patient(NHSNo, Gender, Introduction, Notice) VALUES (?, "
                     "?, ?, ?)").commit(parameters=(self.ID, gender, info, notice))
            return True
        except Exception as e:
            print(e)
            print("Database error")
            return False


if __name__ == "__main__":
    current_user = MenuHelper.login()
    MenuHelper.dispatcher(current_user["username"], current_user["user_type"])
    Patient(current_user).main_menu()
